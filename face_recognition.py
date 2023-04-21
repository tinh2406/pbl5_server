import cv2
import numpy as np
import os 
import urllib.request
import requests
import time
import datetime
import sys
import sqlite3
# sys.path.append('../')
from firestore import addImageToStorage,addHistory,addNotify


# esp32-cam
# count = 0

def recognize_faces(ipESP32):
    print('start recognize_faces')
    def getProfile(id):
        conn = sqlite3.connect('./test.db')

        query = "Select * from faces Where id = "+str(id)

        cursor = conn.execute(query)

        profile = None
        for row in cursor:
            profile=row
        conn.close()
        return profile

    # urlUnlock ='http://192.168.1.7/unlock'
    urlUnlock = f'http://{ipESP32}/unlock'
    # urlImg='http://192.168.1.7/cam-hi.jpg'  
    urlImg= f'http://{ipESP32}/cam-hi.jpg'  
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read('./recognizer/trainningData.xml')
    cascadePath = "./FacialRecognition/haarcascade_frontalface_default.xml"
    # test
    # recognizer.read('./trainer/trainer.yml')
    # cascadePath = "./haarcascade_frontalface_default.xml"
    faceCascade = cv2.CascadeClassifier(cascadePath);
    font = cv2.FONT_HERSHEY_SIMPLEX
    #iniciate id counter
    id = 0
    # names related to ids: example ==> Marcelo: id=1,  etc
    # names = ['None','Duy Nguyen','Obama','Donald Trump'] 
    # Initialize and start realtime video capture
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
    while True:
        if time.time() - start_time > 120:
            print('Recognize faces timeout')
            cam.release()
            cv2.destroyAllWindows()
            return False

        # esp32
        img_resp=urllib.request.urlopen(urlImg)
        imgnp=np.array(bytearray(img_resp.read()),dtype=np.uint8)
        img = cv2.imdecode(imgnp,-1)
        img = cv2.flip(img,1)
        
        # cv2.imshow('live transmission',img)
        #  =================================================================
        # ret, img =cam.read()
        # img = cv2.flip(img, 1) # Flip vertically
        

        gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        
        faces = faceCascade.detectMultiScale( 
            gray,
            scaleFactor = 1.2,
            minNeighbors = 5,
            minSize = (int(minW), int(minH)),
        )
        
        # if (cv2.getTickCount() - pre_time) / cv2.getTickFrequency() < 5:
        #     print('stop detecting')
        # # if (datetime.datetime.now() - pre_time) < 5:
        #     # count += 1
        #     # print('stop detecting ' + str(count))
        #     continue
        # else:
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
                pre_time = cv2.getTickCount()
                pre_time = datetime.datetime.now()
                data = {'data': 'open'}
                response = requests.post(urlUnlock, data=data)
                print(response.status_code)
                # count = 0
                # luu anh vao thu muc imagesSaved
                now = datetime.datetime.now()
                imgTime = now.strftime("%d-%m-%y_%Hh%Mm%Ss")
                imgPathRecognize = "./imagesSaved/" + imgTime +"_"+ name + ".jpg" 
                addHistory(ipESP32,name)
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
                cv2.imwrite(imgPathRecognize, img)
                cam.release()
                cv2.destroyAllWindows()
                print('successfully recognition')
                return True
        if unknown_count >= 500:
            print('day la nguoi la')
            now = datetime.datetime.now()
            imgTimeUnknown = now.strftime("%d-%m-%y_%Hh%Mm%Ss")
            imgPathUnknown = "./unknownImage/" + imgTimeUnknown +"_"+ id + ".jpg" 
            cv2.imwrite(imgPathUnknown,img)
            nameUnknown = "Unknown_" + imgTimeUnknown + ".jpg"

            urlImage = addImageToStorage('notify',imgPathUnknown,nameUnknown)
            addNotify(ipESP32,'Co nguoi la',urlImage)
            unknown_count = 0
            cam.release()
            cv2.destroyAllWindows()
            print('finished recognition: failed')
            return False
        cv2.imshow('camera',img)
        k = cv2.waitKey(10) & 0xff # Press 'ESC' for exiting video
        if k == 27:
            return False
            break

# recognize_faces()
        