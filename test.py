import subprocess

# command = "python facenet/src/classifier.py TRAIN Dataset/FaceData/processed models/20180402-114759.pb models/facemodel.pkl --batch_size 1000"
command = "python facenet/src/classifier.py TRAIN dataSet/processed models/20180402-114759.pb models/facemodel.pkl --batch_size 1000"
command_process_img = "python facenet/src/align_dataset_mtcnn.py  dataSet/raw dataSet/processed --image_size 160 --margin 32  --random_order --gpu_memory_fraction 0.25"
# subprocess.call(command, shell=True)
subprocess.call(command_process_img, shell=True)
