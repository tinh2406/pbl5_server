import subprocess
import importlib

def train():
    print('test')
    command = "python facenet/src/classifier.py TRAIN dataSet models/20180402-114759.pb models/facemodel.pkl --batch_size 1000"
    subprocess.call(command, shell=True)
    import face_rec_cam
    importlib.reload(face_rec_cam)


