import cv2
from threading import Thread,Lock
import time
import logging

VIDEO_FILE = "data/video/campusData.mp4"

use_thread = False
need_flip = False
cap = None
frame = None

# public API
# init(), read_frame(), stop()

def init(res=(320, 240), fps=30, threading=True):
	logging.info("Camera systems initializing...")
	global cap, use_thread, frame, cam_thr

	cap = cv2.VideoCapture(VIDEO_FILE)

	cap.set(3, res[0]) # width
	cap.set(4, res[1]) # height
	cap.set(5, fps)

	# start the camera thread
	if threading:
		use_thread = True
		cam_thr = Thread(target=__update, args=())
		cam_thr.start()
		logging.info("Initializing threads...")
		time.sleep(1.0)
	else:
		logging.info("No threads to initialize!")
	if need_flip == True:
		logging.info("Initializing camera flip...")
	
	logging.info("All camera systems go!")

def __update():
	global frame
	while use_thread:
		ret, tmp_frame = cap.read() # blocking read
		if not ret:
			logging.error("Couldn't read frame from camera. Did the video finish?")
			time.sleep(2)
			continue
		if need_flip == True:
			frame = cv2.flip(tmp_frame, -1)
		else:
			frame = tmp_frame
	logging.info("Camera thread finished!")
	cap.release()
	logging.info("Camera systems completed a full shutdown.")

def read_frame():
	global frame
	if not use_thread and ret == True:
		ret, frame = cap.read() # blocking read
	return frame

def stop():
	global use_thread
	logging.info("Closing the video feed...")
	use_thread = False
	logging.warning("Abrupt camera shutdown!")

if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO)
	init()
	while True:
		frame = read_frame()
		cv2.imshow('frame', frame)
		if cv2.waitKey(10) & 0xFF == ord('q'):
			stop()
			break