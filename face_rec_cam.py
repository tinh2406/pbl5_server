from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf
from imutils.video import VideoStream


import argparse
import facenet
import imutils
import os
import sys
import math
import pickle
import detect_face
import numpy as np
import cv2
import dlib
import collections
import urllib.request
import time
import traceback
import requests
import datetime
from firestore import addImageToStorage,addHistory,addNotify
from imutils import face_utils
from sklearn.svm import SVC
from keras.models import load_model
import sqlite3

# Khởi tạo Model instance

parser = argparse.ArgumentParser()
parser.add_argument('--path', help='Path of the video you want to test on.', default=0)
args = parser.parse_args()

MINSIZE = 20
THRESHOLD = [0.6, 0.7, 0.7]
FACTOR = 0.709
INPUT_IMAGE_SIZE = 160
CLASSIFIER_PATH = 'Models/facemodel.pkl'
VIDEO_PATH = args.path
FACENET_MODEL_PATH = 'Models/20180402-114759.pb'
IMG_SIZE = (34, 26)
IMAGE_SIZE = 182


def getProfile(id):
    conn = sqlite3.connect('./test.db')
    query = "Select * from faces Where id = "+str(id)

    cursor = conn.execute(query)

    profile = None
    for row in cursor:
        profile=row
    conn.close()
    return profile

def crop_eye(gray, eye_points):
    x1, y1 = np.amin(eye_points, axis=0)
    x2, y2 = np.amax(eye_points, axis=0)
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    w = (x2 - x1) * 1
    h = w * IMG_SIZE[1] / IMG_SIZE[0]

    margin_x, margin_y = w / 2, h / 2

    min_x, min_y = int(cx - margin_x), int(cy - margin_y)
    max_x, max_y = int(cx + margin_x), int(cy + margin_y)

    eye_rect = np.rint([min_x, min_y, max_x, max_y]).astype(np.int)

    eye_img = gray[eye_rect[1]:eye_rect[3], eye_rect[0]:eye_rect[2]]

    return eye_img, eye_rect


with open(CLASSIFIER_PATH, 'rb') as file:
    model2, class_names = pickle.load(file)
print("Custom Classifier, Successfully loaded")

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')

with tf.Graph().as_default() as graph2:
    session2 = tf.compat.v1.Session(graph=graph2)
    with session2.as_default():
        # tf.compat.v1.disable_eager_execution()
        model1 = load_model('Models/2018_12_17_22_58_35.h5')
        model1.summary()
with tf.Graph().as_default() as graph1:
    # Cai dat GPU neu co
    gpu_options = tf.compat.v1.GPUOptions(per_process_gpu_memory_fraction=0.6)
    session1 = tf.compat.v1.Session(config=tf.compat.v1.ConfigProto(gpu_options=gpu_options, log_device_placement=False),graph=graph1)
    with session1.as_default():

        # Load the model
        print('Loading feature extraction model')
        tf.compat.v1.disable_eager_execution()
        facenet.load_model(FACENET_MODEL_PATH)

        # Get input and output tensors

        graph = tf.compat.v1.get_default_graph()
        images_placeholder = graph.get_tensor_by_name("input:0")
        embeddings = graph.get_tensor_by_name("embeddings:0")
        phase_train_placeholder = graph.get_tensor_by_name("phase_train:0")
        embedding_size = embeddings.get_shape()[1]

        pnet, rnet, onet = detect_face.create_mtcnn(session1, "facenet/src/align")

        people_detected = set()
        person_detected = collections.Counter()
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read('recognizer/trainningData.xml')
cascadePath = "FacialRecognition/haarcascade_frontalface_default.xml"
# test
# recognizer.read('./trainer/trainer.yml')
# cascadePath = "./haarcascade_frontalface_default.xml"
faceCascade = cv2.CascadeClassifier(cascadePath);
def recognize_faces(ipESP32,phone):
    
    # Load The Custom Classifier

    urlUnlock = f'http://{ipESP32}/unlock'

    print('start recognize_faces')

    # cap  = VideoStream(src=0).start()
    # urlImg= 'http://192.168.1.6/cam-hi.jpg'

    try:
        urlImg= f'http://{ipESP32}/cam-hi.jpg'  
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        #iniciate id counter
        id = 0
        # cam = cv2.VideoCapture(0)
        # cam.set(3, 640) # set video widht
        # cam.set(4, 480) # set video height
        # # Define min window size to be recognized as a face
        # minW = 0.1*cam.get(3)
        # minH = 0.1*cam.get(4)
        imgScale = 0.25
        unknown_count = 0       
        im=None
        # pre_time = cv2.getTickCount()
        start_time = time.time()
        
        blinks = 0
        last_blink_time = time.time()
        eye_privious_right = 0.5
        eye_privious_left = 0.5
        
        while True:
            # esp32
            img_resp=urllib.request.urlopen(urlImg)
            imgnp=np.array(bytearray(img_resp.read()),dtype=np.uint8)
            frame = cv2.imdecode(imgnp,-1)
            frame = imutils.resize(frame, width=600)
            frame = cv2.flip(frame,1)

            # frame = cap.read()
            # frame = imutils.resize(frame, width=600)
            # frame = cv2.flip(frame, 1)

            gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)

            bounding_boxes, _ = detect_face.detect_face(frame, MINSIZE, pnet, rnet, onet, THRESHOLD, FACTOR)

            faces_found = bounding_boxes.shape[0]

            if time.time() - start_time > 120:
                print('Recognize faces timeout')
                finishRecognition(urlUnlock,False)
                now = datetime.datetime.now()
                imgTimeUnknown = now.strftime("%d-%m-%y_%Hh%Mm%Ss")
                imgPathUnknown = "./unknownImage/" + imgTimeUnknown +"_" + "unknown" + ".jpg" 
                cv2.imwrite(imgPathUnknown,frame)
                nameUnknown = "Unknown_" + imgTimeUnknown + ".jpg"
                urlImage = addImageToStorage('notify',imgPathUnknown,nameUnknown)
                addNotify(ipESP32,'Co nguoi la',phone,urlImage)
                # cap.stop()
                cv2.destroyAllWindows()
                return False

            if blinks < 2:
                faces_eyes = detector(gray)
                for face in faces_eyes:
                    shapes = predictor(gray, face)
                    shapes = face_utils.shape_to_np(shapes)

                    eye_img_l, eye_rect_l = crop_eye(gray, eye_points=shapes[36:42])
                    eye_img_r, eye_rect_r = crop_eye(gray, eye_points=shapes[42:48])

                    eye_img_l = cv2.resize(eye_img_l, dsize=IMG_SIZE)
                    eye_img_r = cv2.resize(eye_img_r, dsize=IMG_SIZE)
                    eye_img_r = cv2.flip(eye_img_r, flipCode=1)

                    eye_input_l = eye_img_l.copy().reshape((1, IMG_SIZE[1], IMG_SIZE[0], 1)).astype(np.float32) / 255.
                    eye_input_r = eye_img_r.copy().reshape((1, IMG_SIZE[1], IMG_SIZE[0], 1)).astype(np.float32) / 255.
                    
                    with session2.as_default():
                        with graph2.as_default():
                            pred_l = model1.predict(eye_input_l)
                            pred_r = model1.predict(eye_input_r)

                    # visualize
                    state_l = '%.1f' if pred_l > 0.1 else '%.1f'
                    state_r = '%.1f' if pred_r > 0.1 else '%.1f'

                    state_l = state_l % pred_l
                    state_r = state_r % pred_r
                    color_l = (0,255,0)
                    color_r = ()
                    if float(state_l) > 0.1 :
                        color_l = (0,255,0)
                    else : 
                        color_l = (0,0,255)
                    if float(state_r) > 0.1 :
                        color_r = (0,255,0)
                    else : 
                        color_r = (0,0,255)
                        
                    cv2.rectangle(frame, pt1=tuple(eye_rect_l[0:2]), pt2=tuple(eye_rect_l[2:4]), color=color_l, thickness=2)
                    cv2.rectangle(frame, pt1=tuple(eye_rect_r[0:2]), pt2=tuple(eye_rect_r[2:4]), color=color_r, thickness=2)

                    cv2.putText(frame, state_l, tuple(eye_rect_l[0:2]), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_l, 2)
                    cv2.putText(frame, state_r, tuple(eye_rect_r[0:2]), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_r, 2)
                    
                    
                    if float(state_l) < 0.4 and float(state_r) < 0.4:
                        # if time.time() - last_blink_time < 1:
                        #     continue
                        if eye_privious_right > 0.6 or eye_privious_left > 0.6:
                            blinks += 1
                            last_blink_time = time.time()
                    eye_privious_right = float(state_r)
                    eye_privious_left = float(state_l)
                    print('so lan nhay mat ', blinks)
                    if blinks < 2:
                        cv2.putText(frame, 'Fake Face', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            else:
                try:
                    if faces_found > 1:
                        # chỉ nhận diện khi có một khuôn mặt
                        cv2.putText(frame, "Only one face", (0, 100), cv2.FONT_HERSHEY_COMPLEX_SMALL,
                                    1, (255, 255, 255), thickness=1, lineType=2)
                    elif faces_found > 0:
                        det = bounding_boxes[:, 0:4]
                        # độ dài của bounding box được phát hiện trên khuôn mặt và kích thước của khung hình. 
                        bb = np.zeros((faces_found, 4), dtype=np.int32)
                        for i in range(faces_found):
                            bb[i][0] = det[i][0]
                            bb[i][1] = det[i][1]
                            bb[i][2] = det[i][2]
                            bb[i][3] = det[i][3]
                            # khoảng cách theo chiều dọc  của bounding box
                            print(bb[i][3]-bb[i][1])
                            # chiều dài khung hình
                            print(frame.shape[0])
                            print((bb[i][3]-bb[i][1])/frame.shape[0])
                            # nếu chiều dài bounding box và chiều dài khung hình lớn hơn 1/5 thì mới nhận dạng
                            if (bb[i][3]-bb[i][1])/frame.shape[0]>0.20:
                                cropped = frame[bb[i][1]:bb[i][3], bb[i][0]:bb[i][2], :]
                                scaled = cv2.resize(cropped, (INPUT_IMAGE_SIZE, INPUT_IMAGE_SIZE),
                                                    interpolation=cv2.INTER_CUBIC)
                                scaled = facenet.prewhiten(scaled)
                                scaled_reshape = scaled.reshape(-1, INPUT_IMAGE_SIZE, INPUT_IMAGE_SIZE, 3)
                                feed_dict = {images_placeholder: scaled_reshape, phase_train_placeholder: False}
                                emb_array = session1.run(embeddings, feed_dict=feed_dict)

                                predictions = model2.predict_proba(emb_array)
                                best_class_indices = np.argmax(predictions, axis=1)
                                best_class_probabilities = predictions[
                                    np.arange(len(best_class_indices)), best_class_indices]
                                best_name = class_names[best_class_indices[0]]
                                # tên và độ chính xác
                                print("Name: {}, Probability: {}".format(best_name, best_class_probabilities))


                                if best_class_probabilities > 0.60:
                                    cv2.rectangle(frame, (bb[i][0], bb[i][1]), (bb[i][2], bb[i][3]), (0, 255, 0), 2)
                                    text_x = bb[i][0]
                                    text_y = bb[i][3] + 20

                                    name = class_names[best_class_indices[0]]
                                    cv2.putText(frame, name, (text_x, text_y), cv2.FONT_HERSHEY_COMPLEX_SMALL,
                                                1, (255, 255, 255), thickness=1, lineType=2)
                                    cv2.putText(frame, str(round(best_class_probabilities[0], 3)), (text_x, text_y + 17),
                                                cv2.FONT_HERSHEY_COMPLEX_SMALL,
                                                1, (255, 255, 255), thickness=1, lineType=2)
                                    person_detected[best_name] += 1
                                    finishRecognition(urlUnlock,True)
                                    now = datetime.datetime.now()
                                    imgTime = now.strftime("%d-%m-%y_%Hh%Mm%Ss")
                                    imgPathRecognize = "./imagesSaved/" + imgTime +"_"+ name + ".jpg" 
                                    addHistory(ipESP32,'open by ' + name,phone)
                                    # check = True
                                    unknown_count = 0
                                    cv2.imwrite(imgPathRecognize, frame)
                                    cv2.destroyAllWindows()
                                    print('successfully recognition')
                                    # cap.stop()
                                    return True
                                else:
                                    name = "Unknown"
                                    unknown_count += 1
                except:
                    pass
            if unknown_count >= 50:
                print('day la nguoi la')
                finishRecognition(urlUnlock,False)
                now = datetime.datetime.now()
                imgTimeUnknown = now.strftime("%d-%m-%y_%Hh%Mm%Ss")
                imgPathUnknown = "./unknownImage/" + imgTimeUnknown +"_" + "unknown" + ".jpg" 
                cv2.imwrite(imgPathUnknown,frame)
                nameUnknown = "Unknown_" + imgTimeUnknown + ".jpg"
                urlImage = addImageToStorage('notify',imgPathUnknown,nameUnknown)
                addNotify(ipESP32,'Co nguoi la ',phone,urlImage)
                unknown_count = 0
                cv2.destroyAllWindows()
                print('finished recognition: failed')
                # cap.stop()
                return False
            cv2.imshow('Face Recognition', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                # cap.stop()
                break
    except Exception as e:
        traceback.print_exc()
        print("Loi: " + str(e))
        # finishRecognition(urlUnlock,False)
        # cam.release()
        cv2.destroyAllWindows()
        return False

    # cap.stop()
    cv2.destroyAllWindows()

def finishRecognition(urlUnlock,status):
    if status == True:
        data = {'data': 'open'}
    else:
        data = {'data': 'lock'}
    response = requests.post(urlUnlock, data=data)
    return response
    # return True

# print('kiem tra thuc thi server')
# recognize_faces('192.168.1.6')
