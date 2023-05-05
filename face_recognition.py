import cv2, dlib
import numpy as np
from imutils import face_utils
from keras.models import load_model
import time
import os
import urllib.request
import requests
import time
import datetime
import sys
import sqlite3
from firestore import addImageToStorage,addHistory,addNotify

# sys.path.append('../')
# from firestore import addImageToStorage,addHistory,addNotify
# esp32-cam
# count = 0
def recognize_faces(ipESP32):
    print('start recognize_faces')
    IMG_SIZE = (34, 26)

    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')

    model = load_model('models/2018_12_17_22_58_35.h5')
    model.summary()
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

    try:
        # urlUnlock ='http://192.168.1.7/unlock'
        #urlUnlock = f'http://{ipESP32}/unlock'
        # urlImg='http://192.168.1.7/cam-hi.jpg'  
        #urlImg= f'http://{ipESP32}/cam-hi.jpg'  
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.read('recognizer/trainningData.xml')
        cascadePath = "FacialRecognition/haarcascade_frontalface_default.xml"
        # test
        # recognizer.read('./trainer/trainer.yml')
        # cascadePath = "./haarcascade_frontalface_default.xml"
        faceCascade = cv2.CascadeClassifier(cascadePath);
        font = cv2.FONT_HERSHEY_SIMPLEX
        #iniciate id counter
        id = 0
        cam = cv2.VideoCapture(0)
        cam.set(3, 640) # set video widht
        cam.set(4, 480) # set video height
        # Define min window size to be recognized as a face
        minW = 0.1*cam.get(3)
        minH = 0.1*cam.get(4)
        imgScale = 0.25
        unknown_count = 0       
        im=None
        # pre_time = cv2.getTickCount()
        start_time = time.time()
        
        blinks = 0
        last_blink_time = time.time()
        eye_privious_right = 1
        eye_privious_left = 1

        
        # if not ret:
        #     break
        while True:           
            ret, img =cam.read()
            img = cv2.flip(img, 1) # Flip vertically
            gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
            if time.time() - start_time > 150:
                print('Recognize faces timeout')
                # cam.release()
                # cv2.destroyAllWindows()
                # return False

            # esp32
            # img_resp=urllib.request.urlopen(urlImg)
            # imgnp=np.array(bytearray(img_resp.read()),dtype=np.uint8)
            # img = cv2.imdecode(imgnp,-1)
            # img = cv2.flip(img,1)
        
            # cv2.imshow('live transmission',img)
            #  =================================================================

            # if (cv2.getTickCount() - pre_time) / cv2.getTickFrequency() < 5:
            #     print('stop detecting')
            # # if (datetime.datetime.now() - pre_time) < 5:
            #     # count += 1
            #     # print('stop detecting ' + str(count))
            #     continue
            # else:
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

                    pred_l = model.predict(eye_input_l)
                    pred_r = model.predict(eye_input_r)

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
                        
                    cv2.rectangle(img, pt1=tuple(eye_rect_l[0:2]), pt2=tuple(eye_rect_l[2:4]), color=color_l, thickness=2)
                    cv2.rectangle(img, pt1=tuple(eye_rect_r[0:2]), pt2=tuple(eye_rect_r[2:4]), color=color_r, thickness=2)

                    cv2.putText(img, state_l, tuple(eye_rect_l[0:2]), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_l, 2)
                    cv2.putText(img, state_r, tuple(eye_rect_r[0:2]), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_r, 2)
                    
                    
                    if float(state_l) < 0.5 and float(state_r) < 0.5:
                        # if time.time() - last_blink_time < 1:
                        #     continue
                        if eye_privious_right > 0.5 or eye_privious_left > 0.5:
                            blinks += 1
                            last_blink_time = time.time()
                    eye_privious_right = float(state_r)
                    eye_privious_left = float(state_l)
                    print('so lan nhay mat ', blinks)
                    if blinks < 2:
                        cv2.putText(img, 'Fake Face', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            else: 
                faces = faceCascade.detectMultiScale( 
                        gray,
                        scaleFactor = 1.2,
                        minNeighbors = 5,
                        minSize = (int(minW), int(minH)),
                    )
                check = False
                for(x,y,w,h) in faces:
                    cv2.rectangle(img, (x,y), (x+w,y+h), (0,255,0), 2)
                    id, confidence = recognizer.predict(gray[y:y+h,x:x+w])
                    # Check if confidence is less them 100 ==> "0" is perfect match 
                    if (confidence < 85):
                        name = getProfile(id)[1]
                        confidence = " {0}%".format(round(100 - confidence))
                        # print(name)
                        # print(confidence)
                        #pre_time = cv2.getTickCount()
                        #pre_time = datetime.datetime.now()
                        #data = {'data': 'open'}
                        #response = requests.post(urlUnlock, data=data)
                        #print(response.status_code)
                        # count = 0
                        # luu anh vao thu muc imagesSaved
                        now = datetime.datetime.now()
                        # imgTime = now.strftime("%d-%m-%y_%Hh%Mm%Ss")
                        # imgPathRecognize = "./imagesSaved/" + imgTime +"_"+ name + ".jpg" 
                        # addHistory('192.168.1.5',name)
                        check = True
                        unknown_count = 0
                    else:
                        name = "unknown"
                        confidence = "  {0}%".format(round(100 - confidence))
                        unknown_count += 1
                        # if unknown_count >= 200:
                        #     print("Đây là giả mạo")
                        #     unknown_count = 0
                    # print(str(getProfile(id)))
                    # print(str(confidence))
                    cv2.putText(img, name, (x+5,y-5), font, 1, (255,255,255), 2)
                    cv2.putText(img, str(confidence), (x+5,y+h-5), font, 1, (255,255,0), 1)
                    if check == True:
                        # cv2.imwrite(imgPathRecognize, img)
                        # cam.release()
                        # cv2.destroyAllWindows()
                        print('successfully recognition')
                        # return True
                if unknown_count >= 200:
                    print('day la nguoi la')
                    now = datetime.datetime.now()
                    imgTimeUnknown = now.strftime("%d-%m-%y_%Hh%Mm%Ss")
                    imgPathUnknown = "./unknownImage/" + imgTimeUnknown +"_" + "unknown" + ".jpg" 
                    cv2.imwrite(imgPathUnknown,img)
                    # nameUnknown = "Unknown_" + imgTimeUnknown + ".jpg"

                    # urlImage = addImageToStorage('notify',imgPathUnknown,nameUnknown)
                    # addNotify('192.168.1.5','Co nguoi la',urlImage)
                    unknown_count = 0
                    # cam.release()
                    # cv2.destroyAllWindows()
                    print('finished recognition: failed')
                    # return False
                    

                    # reset blink count if no blinks detected in the last 5 seconds
                    # if time.time() - last_blink_time > 5:
                    #     blinks = 0
            cv2.imshow('camera',img)
            k = cv2.waitKey(10) & 0xff # Press 'ESC' for exiting video
            if k == 27:
                return False
                break
                              
    except Exception as e:
            print("Loi: " + str(e))
            cam.release()
            cv2.destroyAllWindows()
            return False
        
recognize_faces('192.168.1.5')

