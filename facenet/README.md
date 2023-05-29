

Article link: http://miai.vn/2019/09/11/face-recog-2-0-nhan-dien-khuon-mat-trong-video-bang-mtcnn-va-facenet/

<br> tải về <a href='https://drive.google.com/file/d/1EXPBSXwTaqrSC0OhUdXNmKSh9qJUQ55-/view'>tại đây</a> và giải nén vào thư mục Models 

Chạy để huấn luyện khi nào có thêm người : 
python src/classifier.py TRAIN Dataset/FaceData/processed Models/20180402-114759.pb Models/facemodel.pkl --batch_size 1000

<br>chạy file face_rec_cam.py để chạy nhận dạng


