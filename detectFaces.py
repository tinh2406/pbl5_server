import os
import cv2
def getFace(img,phone,name,count):
    
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_frontalface_default.xml")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(gray,     
        scaleFactor=1.1, minNeighbors=5)
    if(len(faces)>0):
        print("có mặt")
        (x,y,w,h)=faces[0]
        if w>1200 and h>1200:
            if not os.path.exists('./dataSet'):
                os.makedirs('./dataSet')
            if not os.path.exists(f"./dataSet/{phone}"):
                os.mkdir(f"./dataSet/{phone}")
            if not os.path.exists(f"./dataSet/{phone}/{name}"):
                os.mkdir(f"./dataSet/{phone}/{name}")
            cv2.imwrite(f"./dataSet/{phone}/{name}/{count}.png",gray[y:y+h,x:x+w])
            print(count)
            return True
    print("không mặt")
    return False
