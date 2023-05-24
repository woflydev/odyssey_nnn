from pydualsense import *
from utils.motor_lib.driver import *
import params as params
from importlib import import_module
import time
import logging
import cv2
# requires libhidapi-dev

#---------------------#
# Camera Config 			#
#---------------------#
CAMERA_FPS = 30
CAMERA_RESOLUTION = (320, 240)
VIDEO_FEED = False
USE_THREADING = True
RECORD_DATA = True

#---------------------#
# System Variables		#
#---------------------#
frame_id = 0
angle = 0.0
period = 0.05 # sec (=50ms)

#---------------------#
# Console Logging			#
#---------------------#
logging.basicConfig(level=logging.INFO)

LIMIT = 0.95

camera = import_module(params.camera)

def startup_signal(iterations, delay):
	BLINK_DELAY = 0.2
	for i in range(iterations):
		try:
			drivePin(15, 100)
			time.sleep(BLINK_DELAY)
			drivePin(15, 0)
			time.sleep(delay)
			drivePin(15, 100)
			time.sleep(BLINK_DELAY)
			drivePin(15, 0)
		except:
			logging.warning("Driver not initialized.")

ds = pydualsense() 		# open controller
ds.init() 			# initialize controller

ds.light.setColorI(0,255,0) 	# set touchpad color to red
ds.triggerL.setMode(TriggerModes.Rigid)
ds.triggerR.setMode(TriggerModes.Pulse)
ds.conType.BT = False 		# set connection type to bluetooth

startup_signal(2, 0.1)

camera.init(res=CAMERA_RESOLUTION, fps=CAMERA_FPS, threading=USE_THREADING)

fourcc = cv2.VideoWriter_fourcc(*'MP4V')
vidfile = cv2.VideoWriter(params.rec_vid_file, fourcc, CAMERA_FPS, CAMERA_RESOLUTION)

while True:
		frame = camera.read_frame()
		ts = time.time()

		left = (ds.state.LY / 128 * 100) * LIMIT
		right = (ds.state.RY / 128 * 100) * LIMIT
		light = ds.state.L1 * 100 # ds.state.L2 ** 2 / (16384 / 25) # gradual control

		if ds.state.R1 == 1:              # brake with R1
				left = 0
				right = 0
				print(f'Brake: [{left}, {right}]')

		if ds.state.R2 > 16:              # coast with R2
				left = 0
				right = 0
				print(f'Coast: [{left}, {right}]')
				off()

		if ds.state.cross == 1:            # exit with cross
				left = 0
				right = 0
				print(f'[{left}, {right}]')
				off()
				print("Stopped.")
				quit()

		if RECORD_DATA == True and frame_id == 0:
			# create files for data recording
			keyfile = open(params.rec_csv_file, 'w+')
			keyfile.write("ts,frame,wheel\n") # ts (ms)

		if RECORD_DATA == True and frame is not None:
			# increase frame_id
			frame_id += 1

			# write input (angle)
			str = "{},{},{}\n".format(int(ts*1000), frame_id, angle)
			keyfile.write(str)

			# write video stream
			vidfile.write(frame)

			#img_name = "cal_images/opencv_frame_{}.png".format(frame_id)
			#cv2.imwrite(img_name, frame)
			if frame_id >= 1000:
				print ("recorded 1000 frames")
				camera.stop()
				break
			print("%.3f %d %.3f %d(ms)" % (ts, frame_id, angle, int((time.time() - ts)*1000)))

		#print(f'[{left}, {right}]')
		move(-left, -right)
		#drivePin(15, 0)
