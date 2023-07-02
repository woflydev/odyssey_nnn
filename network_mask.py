import tensorflow as tf
import keras
import numpy as np
import cv2

model = keras.models.load_model('data/segmentation2.h5')
source = "C:\\Users\\wolfy\\Desktop\\odyssey_nnn\\data\\video\\TestTrack.mp4"
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open camera")
    exit()

while True:
  # Capture frame-by-frame
  ret, frame = cap.read()
  # if frame is read correctly ret is True
  if not ret:
    print("Can't receive frame (stream end?). Exiting ...")
    break
  
  cv2.imshow('original', frame)
  frame = cv2.resize(frame, (360, 180))
  frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
  frame = (frame / 255)
  tensor = tf.convert_to_tensor([frame])
  # Display the resulting frame

  predicted_mask = model.predict(tensor)[0] * 255
  cv2.imshow('predicted', predicted_mask)

  if cv2.waitKey(1) == ord('q'):
    break
# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()