import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import messaging
from firebase_admin import storage
from google.cloud import storage as gc_storage
import random
import json
import datetime
# Use a service account.
# cred = credentials.Certificate('./serviceAccount.json')
cred = credentials.Certificate('./serviceAccount.json')

app = firebase_admin.initialize_app(cred, {
    'storageBucket': 'pbl5-40150.appspot.com'
})

db = firestore.client()

bucket = storage.bucket()



def addUserOwner(phone,name,password,addressDoor,addressBluetooth):
   doc_ref = db.collection('users').document(phone)
   doc_ref.set({
   'name': name,
   'password': password,
   'addressDoor': addressDoor,
   'owner':True
})

def addUser(phone,name,phoneOwner):
   users_ref = db.collection('users').document(phone)
   doc = users_ref.get().to_dict()
   if doc!=None:
      time = datetime.datetime.now() + datetime.timedelta(minutes=10,hours=-7)
      doc_ref = db.collection('verifys').document(phone)
      doc_ref.set({"code":random.randint(10000,99999),"expireAt":time})
      return "exists account"

   users_ref = db.collection('users').document(phoneOwner)
   doc = users_ref.get().to_dict()
   if doc == None:
      return "no have owner"
   
   addressDoor = doc["addressDoor"]

   password = random.randint(10000,99999)

   doc_ref = db.collection('users').document(phone)
   doc_ref.set({
   'name': name,
   'password': str(password),
   'addressDoor': addressDoor,
   'owner':False})
   return password



def addUserExists(phone,name,phoneOwner,verification):
   users_ref = db.collection('verifys').document(phone)
   doc = users_ref.get().to_dict()
   if doc==None:
      return "error"

   if str(doc["code"])!=verification or datetime.datetime.fromtimestamp(doc["expireAt"].timestamp())<datetime.datetime.now():
      return "verification code not match"
   
   users_ref = db.collection('users').document(phoneOwner)
   doc = users_ref.get().to_dict()
   if doc == None:
      return "no have owner"
   
   addressDoor = doc["addressDoor"]

   password = random.randint(10000,99999)
   db.collection('verifys').document(phone).delete()
   doc_ref = db.collection('users').document(phone)
   doc_ref.set({
   'name': name,
   'password': str(password),
   'addressDoor': addressDoor,
   'owner':False})
   return password

def resetVerifyCode(phone):
   users_ref = db.collection('users').document(phone)
   doc = users_ref.get().to_dict()
   if doc==None:
      return False
   time = datetime.datetime.now() + datetime.timedelta(minutes=10,hours=-7)
   doc_ref = db.collection('verifys').document(phone)
   doc_ref.set({"code":random.randint(10000,99999),"expireAt":time})
   return True


def updatePassword(phone,password,newPassword):
   users_ref = db.collection('users').document(phone)
   doc = users_ref.get().to_dict()
   if doc == None or doc["password"]!=password:
      return False
   doc["password"] = newPassword

   users_ref.set(doc)
   return True

def addHistory(device,message):
   devices_ref = db.collection('devices').document(device)
   time = datetime.datetime.now() + datetime.timedelta(hours=-7)
   db.collection('historys').document().set({'device':devices_ref,"message":message,'createAt':time})

def addNotify(device,message,urlImage):
   devices_ref = db.collection('devices').document(device)
   time = datetime.datetime.now() + datetime.timedelta(hours=-7)
   res = db.collection('notifys').add({'device':devices_ref,"message":message,'createAt':time,'urlImgae':urlImage})
   docs = db.collection("users").where('addressDoor','array_contains',devices_ref).stream()
   
   devices = []

   for i in docs:
      try:
         tokens = db.collection('tokens').document(i.id).get().to_dict()["devices"]
         devices.extend(tokens)
      except Exception:
         print()


   notification = messaging.Notification(
      title='Thông báo', 
      # body=(json.dumps({"message":message,"id":res[1].id}))),
      body=message,
      )
      
   

# Gửi thông báo với Notification này
   message = messaging.MulticastMessage(
      notification=notification,
      data={
         "id":res[1].id
      },
      tokens=devices
   )

   response = messaging.send_multicast(message)
   return True


def addHistory(device,user,message = 'thong bao'):
   devices_ref = db.collection('devices').document(device)
   time = datetime.datetime.now() + datetime.timedelta(hours=-7)
   db.collection('historys').document().set({'device':devices_ref,"message":message,'createAt':time,'user':user})

   docs = db.collection("users").where('addressDoor','array_contains',devices_ref).stream()
   
   devices = []

   for i in docs:
      tokens = db.collection('tokens').document(i.id).get().to_dict()["devices"]
      devices.extend(tokens)

   notification = messaging.Notification(
      title='Thông báo',
      body=message
      )
   
   message = messaging.MulticastMessage(
      notification=notification,
      tokens=devices
   )

   response = messaging.send_multicast(message)
   return True

def testing ():
   print('this is test')

def addImageToStorage(folderInStorage,path,name):
    folder_path = f'{folderInStorage}/'
    file_name_path = f'{folder_path}{name}'
    blob = bucket.blob(file_name_path)
    blob.upload_from_filename(path)
    print(f'Image has been uploaded to {blob.public_url}')
    return blob.public_url

# image_url = addImageToStorage('notify','./FacialRecognition/imagesSaved/31-03-23_12h26m14s_Duy Nguyen.jpg', 'image_1')
# print(addHistory('192.168.1.113','duy duc nguyen'))
def deviceIsInPhone(device,phone):
   devices_ref = db.collection('devices').document(device)
   docs = db.collection("users").where('addressDoor','array_contains',devices_ref).get()

   for i in docs:
      if i.id==phone:
         return True
   return False

def setStatusDoor(device,status):
   device_ref = db.collection('devices').document(device)
   device_ref.set({'status':status},merge=True)


def getUserByPhone(phone):
   user_ref = db.collection('users').document(phone)
   doc = user_ref.get()
   return doc.to_dict()
def getNameDevice(device):
   device_res = db.collection('devices').document(device)
   doc = device_res.get().to_dict()
   if doc['name']=="":
      return device
   return doc['name']

def updataIPfirebase(phone,preIp,curIP):
   doc_ref = db.collection('deviceUser').document(phone)
   doc_data = doc_ref.get().to_dict()
   if doc_data==None:
      return
   newDevices = []
   for device in doc_data['devices']:
      if device.get().id==preIp:
         device_ref = db.collection('devices').document(curIP)
         newDevices.append(device_ref)
      else:
         newDevices.append(device)
   doc_ref.set({
      "devices": newDevices
   })
   # for doc in doc_data:
   #    d = doc.to_dict()
   #    print(d)
   # Lấy giá trị của trường 'devices'
   
   # doc_ref.update({
   #  'devices': firestore.ArrayUnion(['/devices/' + preIp]),
   #  'devices': firestore.ArrayRemove(['/devices/' + curIP])
   # })
   # print(doc_ref)
   return True

updataIPfirebase('0912459841','192.168.1.5','192.168.1.6')

   
