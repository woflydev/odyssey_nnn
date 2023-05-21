import cv2
from threading import Thread,Lock
import time

use_thread = False
need_flip = False
cap = None
frame = None

# public API
# init(), read_frame(), stop()

def init(res=(320, 240), fps=30, threading=True):
	print ("INFO: Initializing camera...")
	global cap, use_thread, frame, cam_thr

	cap = cv2.VideoCapture("data/video/TestTrack.mp4")

	cap.set(3, res[0]) # width
	cap.set(4, res[1]) # height
	cap.set(5, fps)

	# start the camera thread
	if threading:
		use_thread = True
		cam_thr = Thread(target=__update, args=())
		cam_thr.start()
		print("INFO: Initializing threads...")
		time.sleep(1.0)
	else:
		print("INFO: No threads to initialize!")
	if need_flip == True:
		print("INFO: Initializing camera flip...")
	
	print("INFO: Camera initialized, vision is go!")

def __update():
	global frame
	while use_thread:
		ret, tmp_frame = cap.read() # blocking read
		if not ret:
			print("ERROR: Couldn't read frame from camera.")
			break
		if need_flip == True:
			frame = cv2.flip(tmp_frame, -1)
		else:
			frame = tmp_frame
	print("INFO: Camera thread finished!")
	cap.release()

def read_frame():
	global frame
	if not use_thread:
		ret, frame = cap.read() # blocking read
	return frame

def stop():
	global use_thread
	print("INFO: Closing the video feed...")
	use_thread = False

if __name__ == "__main__":
	init()
	while True:
		frame = read_frame()
		cv2.imshow('frame', frame)
		if cv2.waitKey(10) & 0xFF == ord('q'):
			stop()
			break