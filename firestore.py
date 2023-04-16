import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import messaging
import random
import json
import datetime
# Use a service account.
cred = credentials.Certificate('./serviceAccount.json')

app = firebase_admin.initialize_app(cred)

db = firestore.client()





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

def addNotify(device,message):
   devices_ref = db.collection('devices').document(device)
   time = datetime.datetime.now() + datetime.timedelta(hours=-7)
   res = db.collection('notifys').add({'device':devices_ref,"message":message,'createAt':time})
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
   