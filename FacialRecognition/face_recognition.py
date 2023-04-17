import cv2
import numpy as np
import os 
import urllib.request
import requests
import time
import datetime
import sys
sys.path.append('../')
from firestore import addImageToStorage,addHistory,addNotify
# from tensorflow.keras.models import model_from_json
# from tensorflow.keras.applications import EfficientNetB0
# from tensorflow.keras.applications.efficientnet import preprocess_input
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read('trainer/trainer.yml')
cascadePath = "haarcascade_frontalface_default.xml"
faceCascade = cv2.CascadeClassifier(cascadePath);
font = cv2.FONT_HERSHEY_SIMPLEX
#iniciate id counter
id = 1
# names related to ids: example ==> Marcelo: id=1,  etc
names = ['None','Duy Nguyen','Obama','Donald Trump'] 
# Initialize and start realtime video capture
cam = cv2.VideoCapture(0)
cam.set(3, 640) # set video widht
cam.set(4, 480) # set video height
# Define min window size to be recognized as a face
minW = 0.1*cam.get(3)
minH = 0.1*cam.get(4)
imgScale = 0.25

# esp32-cam
urlImg='http://192.168.1.7/cam-hi.jpg'
urlUnlock ='http://192.168.1.7/unlock'
im=None
unknown_count = 0
# cv2.namedWindow("live transmission", cv2.WINDOW_AUTOSIZE)

pre_time = cv2.getTickCount()
count = 0
# # Load Anti-Spoofing Model graph
# json_file = open('../antispoofing_models/antispoofing_model.json', 'r')
# loaded_model_json = json_file.read()
# json_file.close()
# model = model_from_json(loaded_model_json)
# # load antispoofing model weights
# model.load_weights('../antispoofing_models/antispoofing_model.h5')


while True:
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
        if (confidence < 65):
            id = names[id]
            confidence = " {0}%".format(round(100 - confidence))
            print(id)
            print(confidence)
            pre_time = cv2.getTickCount()
            # pre_time = datetime.datetime.now()
            data = {'data': 'open'}
            response = requests.post(urlUnlock, data=data)
            print(response.status_code)
            count = 0
            now = datetime.datetime.now()
            imgTime = now.strftime("%d-%m-%y_%Hh%Mm%Ss")
            imgPathRecognize = "./imagesSaved/" + imgTime +"_"+ id + ".jpg" 
            addHistory('192.168.1.113',id)
            check = True
            unknown_count = 0
        else:
            id = "unknown"
            confidence = "  {0}%".format(round(100 - confidence))
            unknown_count += 1
            # if unknown_count >= 200:
            #     print("Đây là giả mạo")
            #     unknown_count = 0
        cv2.putText(img, str(id), (x+5,y-5), font, 1, (255,255,255), 2)
        # cv2.putText(img, str(confidence), (x+5,y+h-5), font, 1, (255,255,0), 1)
        if check == True:
            cv2.imwrite(imgPathRecognize, img)
    if unknown_count >= 25:
        print('day la nguoi la')
        now = datetime.datetime.now()
        imgTimeUnknown = now.strftime("%d-%m-%y_%Hh%Mm%Ss")
        imgPathUnknown = "./unknownImage/" + imgTimeUnknown +"_"+ id + ".jpg" 
        cv2.imwrite(imgPathUnknown,img)
        nameUnknown = "Unknown_" + imgTimeUnknown + ".jpg"
        urlImage = addImageToStorage('notify',imgPathUnknown,nameUnknown)
        addNotify('192.168.1.113','Co nguoi la',urlImage)
        unknown_count = 0
    cv2.imshow('camera',img)
    k = cv2.waitKey(10) & 0xff # Press 'ESC' for exiting video
    if k == 27:
        break
        
# Do a bit of cleanup
print("\n [INFO] Exiting Program and cleanup stuff")
cam.release()
cv2.destroyAllWindows()