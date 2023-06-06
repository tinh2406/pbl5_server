import os
import cv2
import numpy as np
from face_rec_cam import findFace
from PIL import Image
from facenet import to_rgb
import tensorflow as tf
from detect_face import detect_face,create_mtcnn
import imutils

with tf.Graph().as_default():
        # gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=gpu_memory_fraction)
        sess =tf.compat.v1.Session()
        with sess.as_default():
            pnet, rnet, onet = create_mtcnn(sess, None)
    
minsize = 20  # minimum size of face
threshold = [0.6, 0.7, 0.7]  # three steps' threshold
factor = 0.709  # scale factor


def getFace(img,phone,name,count):
    img = imutils.resize(img, width=600)
    img = cv2.flip(img,1)

    status,_ = align_face(img)
    
    if status==False:
        return _

    if not os.path.exists('./dataSet'):
        os.makedirs('./dataSet')
    if not os.path.exists(f"./dataSet/{phone}"):
        os.mkdir(f"./dataSet/{phone}")
    if not os.path.exists(f"./dataSet/{phone}/{name}"):
        os.mkdir(f"./dataSet/{phone}/{name}")
    
    cv2.imwrite(f"./dataSet/{phone}/{name}/{count}.png",_)
    print(count)
    return True



def align_face(image, image_size=160, margin=32, gpu_memory_fraction=0.25):

    img = np.copy(image)

    if img.ndim < 2:
        raise ValueError('Unable to align image: input image has incorrect shape.')
    if img.ndim == 2:
        img = to_rgb(img)
    img = img[:, :, 0:3]

    bounding_boxes, _ = detect_face(img, minsize, pnet, rnet, onet, threshold, factor)
    width = int(bounding_boxes[0][2] - bounding_boxes[0][0] + 1)
    height = int(bounding_boxes[0][3] - bounding_boxes[0][1] + 1)
    if len(bounding_boxes)!=1:
        return False,"Không có mặt"
    if width<200 and height<300:
        return False,"Gần chút nữa"
    
    nrof_faces = bounding_boxes.shape[0]
    if nrof_faces > 0:
        det_arr = []
        img_size = np.asarray(img.shape)[0:2]
        if nrof_faces > 1:
            for i in range(nrof_faces):
                det_arr.append(np.squeeze(bounding_boxes[i]))
        else:
            det_arr.append(np.squeeze(bounding_boxes))

        for i, det in enumerate(det_arr):
            det = np.squeeze(det)
            bb = np.zeros(4, dtype=np.int32)
            bb[0] = np.maximum(det[0] - margin / 2, 0)
            bb[1] = np.maximum(det[1] - margin / 2, 0)
            bb[2] = np.minimum(det[2] + margin / 2, img_size[1])
            bb[3] = np.minimum(det[3] + margin / 2, img_size[0])
            cropped = img[bb[1]:bb[3], bb[0]:bb[2], :]
            cropped = Image.fromarray(cropped)
            scaled = cropped.resize((image_size, image_size), Image.BILINEAR)
            return True,np.array(scaled)
