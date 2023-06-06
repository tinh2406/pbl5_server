import os
import cv2
import numpy as np
from face_rec_cam import findFace

def getFace(img,phone,name,count):
    bounding_boxes,_ = findFace(img)
    x = int(bounding_boxes[0][0])
    y = int(bounding_boxes[0][1])
    width = int(bounding_boxes[0][2] - bounding_boxes[0][0] + 1)
    height = int(bounding_boxes[0][3] - bounding_boxes[0][1] + 1)
    if len(bounding_boxes)!=1:
        return "Không có mặt"
    if width<200 and height<300:
        return "Gần chút nữa"
    if not os.path.exists('./dataSet'):
        os.makedirs('./dataSet')
    if not os.path.exists(f"./dataSet/{phone}"):
        os.mkdir(f"./dataSet/{phone}")
    if not os.path.exists(f"./dataSet/{phone}/{name}"):
        os.mkdir(f"./dataSet/{phone}/{name}")
    cv2.imwrite(f"./dataSet/{phone}/{name}/{count}.png",img)
    print(count)
    return True


# def firstHanle(img):
#     height, width, _ = img.shape
#     gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
#     clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    
#     faces = face_cascade.detectMultiScale(gray,scaleFactor=1.1, minNeighbors=5)

#     if len(faces)>0:
#         (x,y,w,h)=faces[0]
#         if w<200 and h<200:
#             return "Gan chut nua"
#         if w>200 and h>200:
#             eyes = eye_cascade.detectMultiScale(gray[y:y+h,x:x+w])
            
#             if len(eyes)>1:
#                 angle=20
#                 for i in range(len(eyes)):
#                     x=eyes[i][0]-eyes[i-1][0]
#                     y=eyes[i][1]-eyes[i-1][1]
#                     angle2 = np.arctan2(y, x) * 180 / np.pi # tính góc quay theo trục z
#                     if abs(angle)>abs(angle2):
#                         angle=angle2
#                 center = (width / 2, height / 2)
#                 M = cv2.getRotationMatrix2D(center, angle, 1) # tạo ma trận quay
#                 rotated_img = cv2.warpAffine(gray, M, (width, height))
#                 faces = face_cascade.detectMultiScale(rotated_img)
#                 if len(faces)<1:
#                     return "Khong co mat"
#                 for (x,y,w,h) in faces:
#                     if w<200 and h<200:
#                         return "Gan chut nua"
#                     if w>200 and h>200:
#                         gray = clahe.apply(rotated_img[y:y+h,x+15*w//100:x+85*w//100])
#             else:
#                 return "Khong co mat"

#             new_width = 200
#             new_height = int(gray.shape[0] / gray.shape[1] * new_width)
#             gray = cv2.resize(gray, (new_width, new_height), interpolation = cv2.INTER_LINEAR)
#             return gray
#     return "Khong co mat"        