from flask import Flask, request, jsonify,send_file,send_from_directory
import os
import base64
import cv2
import io
import numpy as np
import requests
from PIL import Image
import json
import time
from sqlite import insert,getNameFaceWithPhone,getNamePhonewithId,deleteFaceWithId
from trainData import train
# from face_recognition import recognize_faces
from face_rec_cam import recognize_faces
from sqlite import insert, getNameFaceWithPhone, getNamePhonewithId, deleteFaceWithId
from detectFaces import getFace
from firestore import *
# from firestore import updatePassword,addUser,addUserExists,resetVerifyCode,deviceIsInPhone,setStatusDoor,addHistory,getUserByPhone,getNameDevice,updataIPfirebase
# from firestore import deleteUser, getUserList, updatePassword, addUser, addUserExists, resetVerifyCode, deviceIsInPhone, setStatusDoor, addHistory, getUserByPhone, getNameDevice
app = Flask(__name__)

cam = cv2.VideoCapture(0)
cam.set(3, 640) # set video widht
cam.set(4, 480)

@app.route("/")
def home():
    return "You can post to /api/upload."


@app.route("/users/updatePassword", methods=["POST"])
def updatePasswordAPI():
    data = request.get_json()
    if updatePassword(data["phone"], data["password"], data["newPassword"]):
        return jsonify({"message": "Update password successfully"})
    return jsonify({"message": "Password unchanged"}), 403


@app.route("/users/userList", methods=["GET"])
def getUserListAPI():
    res = getUserList()
    return jsonify(res)


@app.route("/users/addUser", methods=["POST"])
def addUserAPI():
    data = request.get_json()
    res = addUser(data["phone"], data["name"],
                  data["phoneOwner"])
    if res == "exists account" or res == "no have owner":
        return jsonify({"message": res})
    return jsonify({"message": "Add account successfully"})


@app.route("/users/deleteUser", methods=["POST"])
def deleteUserAPI():
    data = request.get_json()
    res = deleteUser(data["phone"])
    return jsonify({"message": res})


@app.route("/users/addUserExists", methods=["POST"])
def addUserExistsAPI():
    data = request.get_json()
    res = addUserExists(data["phone"], data["name"],
                        data["phoneOwner"], data["verification"])
    if res == "error" or res == "verification code not match" or res == "no have owner":
        return jsonify({"message": res})
    return jsonify({"message": "Add account successfully"})


@app.route("/users/resendVerifyCode", methods=["POST"])
def resendVerifyCode():
    data = request.get_json()
    res = resetVerifyCode(data["phone"])
    if res:
        return jsonify({"message": "Resend success"})
    return jsonify({"message": "Resend error"})


@app.route("/users/addUserOwner", methods=["POST"])
def addUserOwner():
    data = request.get_json()

    return "abc"


@app.route("/faces/<id>", methods=["DELETE"])
def deleteFaceAPI(id):
    faces = getNamePhonewithId(id)
    if len(faces) == 0:
        return jsonify({"error": "face not found"}), 404
    face = faces[0]
    deleteFaceWithId(id)
    path = "./dataSet/"+face["phone"]+"/"+face["name"]
    for root, dirs, files in os.walk(path):
        for file in files:
            os.remove(os.path.join(root, file))
    try:
        os.rmdir(path)
    except:
        print("")
    train()
    return jsonify({"message": "face deleted successfully"}), 200


@app.route("/face/<phone>", methods=["GET"])
def getFacesAPI(phone):
    return jsonify({"data": getNameFaceWithPhone(phone)})


@app.route("/api/upload", methods=["POST"])
def upload():
    data = request.get_json()
    phone = data["phone"]
    name = data["name"]
    count = int(data["count"])
    image = data["image"]

    npImage = np.array(Image.open(
        io.BytesIO(base64.b64decode(image))), 'uint8')

    resGetFace = getFace(cv2.flip(cv2.rotate(
        npImage, cv2.ROTATE_90_COUNTERCLOCKWISE), 1), phone, name, count)
    if resGetFace == "Gan chut nua":
        return jsonify({"message": "Gan chut nua"})
    if resGetFace == True:
        if count >= 5:
            insert(name, phone)
            train()
            return jsonify({"message": "success"})
        else:
            return jsonify({"message": "need further data"})
    return jsonify({"message": "khong co mat"})


@app.route('/lockDoor', methods=['POST'])
def lockDoor():
    data = request.get_json()
    phone = data['phone']
    addressDoor = data['addressDoor']
    print(phone)
    print(addressDoor)
    
    if not deviceIsInPhone(addressDoor, phone):
        return jsonify({'message': 'unauthorized'}), 400
    data ={"data": "lock" }
    response = requests.post(f'http://{addressDoor}/unlock',data= data)

    setStatusDoor(addressDoor,True)
    # addHistory(addressDoor,getNameDevice(addressDoor)+' open by '+getUserByPhone(phone)['name'])
    addHistory(addressDoor, getNameDevice(addressDoor) +
               ' open by '+getUserByPhone(phone)['name'])
    print('locked')
    return jsonify({'message': "locked"})


@app.route('/unlockDoor', methods=['POST'])
def unlockDoor():
    data = request.get_json()
    phone = data['phone']
    addressDoor = data['addressDoor']
 
    if not deviceIsInPhone(addressDoor, phone):
        return jsonify({'message': 'unauthorized'}), 400
    
    data ={"data": "open" }
    response = requests.post(f'http://{addressDoor}/unlock',data= data)
    setStatusDoor(addressDoor,False)
    print('Unlocked')
    # return jsonify({'status': response.status_code})
    return jsonify({'message': "unlocked"})


@app.route('/get_image',methods=['GET'])
def get_image():
    cam = cv2.VideoCapture(0)
    cam.set(3, 640) # set video widht
    cam.set(4, 480)
    ret, img =cam.read()
    img = cv2.flip(img, 1)
    # cv2.imwrite('./temp.jpg', img)
    # return send_file('./temp.jpg',mimetype='image/jpeg')
    # Lấy đường dẫn thư mục hiện tại của server
    cur_dir = os.getcwd()
    
    # Lưu ảnh vào một file tạm trong thư mục gốc của ứng dụng Flask
    cv2.imwrite(os.path.join(cur_dir, 'temp.jpg'), img)
    
    cam.release()
    # Trả về file tạm đó cho client
    return send_file(os.path.join(cur_dir, 'temp.jpg'), mimetype='image/jpeg')
    
@app.route('/callapi',methods = ['GET'])
def callapi():
    print('done call api')
    return 'return ket quadjk jkkjsd'

@app.route('/recognize_face',methods = ['POST'])
def handle_recognize_face():
    print('co yeu cau')
    ipAddressESP = request.get_data(as_text=True)
    print('Received data:', ipAddressESP)
    # urlUnlock ='http://192.168.1.7/unlock'
    # data = {'data': 'open'}
    # time.sleep(10)
    # response = requests.post(urlUnlock, data=data)
    check = recognize_faces(ipAddressESP)
    return 'True'

@app.route('/getWifi',methods=['GET'])
def getWifi():
    url = 'http://192.168.1.7/getWifiAddress'
    response = requests.post(url)
    print(response.text)
    return jsonify({'message': response.text})

@app.route('/getBluetooth',methods=['GET'])
def getBluetooth():
    url = 'http://192.168.1.7/getBluetoothAddress'
    response = requests.post(url)
    print(response.text)
    return jsonify({'message': response.text})

@app.route('/updateIP', methods=['POST'])
def updateIP():
    data = request.get_data(as_text=True)
    my_dict = json.loads(data)
    phone = my_dict['phone']
    preIP = my_dict['previousIP']
    curIP = my_dict['currentIP']
    print(phone)
    print(preIP)
    print(curIP)
    status = updataIPfirebase(phone,preIP,curIP)
    print(status)
    return jsonify({'message': 'success'}) 

@app.route('/updateIP1', methods=['POST'])
def updateIP1():
    updataIPfirebase('0912459841','192.168.1.5','192.168.1.1')
    return jsonify({"message":"Password unchanged"})

if __name__ == "__main__":
    app.run(debug=True, host="192.168.43.140", port=os.environ.get("PORT", 3000))

