#!/usr/bin/python
import os
import time
import atexit
import cv2
import math
import numpy as np
import sys
import params
import argparse
import logging

from utils.motor_lib.driver import move, off, drivePin

from PIL import Image, ImageDraw

##########################################################
# import car's sensor/actuator modules
##########################################################
camera   = __import__(params.camera)
#actuator = __import__(params.actuator)
inputdev = __import__(params.inputdev)

##########################################################
# global variable initialization
##########################################################
BASE_SPEED = 40

#---------------------#
# Camera Config 			#
#---------------------#
CAMERA_FPS = 30
CAMERA_RESOLUTION = (320, 240)
VIDEO_FEED = False
USE_THREADING = True
RECORD_DATA = False

#---------------------#
# Network Config 			#
#---------------------#
USE_NETWORK = False
FPV_VIDEO = False # only works if USE_NETWORK is true

#---------------------#
# System Variables		#
#---------------------#
frame_id = 0
angle = 0.0
period = 0.05 # sec (=50ms)

##########################################################
# local functions
##########################################################
def deg2rad(deg):
	return deg * math.pi / 180.0
def rad2deg(rad):
	return 180.0 * rad / math.pi

def starup_signal(iterations, delay):
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

def g_tick():
	t = time.time()
	count = 0
	while True:
		count += 1
		yield max(t + count*period - time.time(),0)

def turn_off():
	#actuator.stop()
	off()
	camera.stop()
	drivePin(15, 0)
	if frame_id > 0:
		keyfile.close()
		vidfile.release()

def crop_image(img):
	scaled_img = cv2.resize(img, (max(int(params.img_height * 4 / 3), params.img_width), params.img_height))
	fb_h, fb_w, fb_c = scaled_img.shape
	# print(scaled_img.shape)
	startx = int((fb_w - params.img_width) / 2);
	starty = int((fb_h - params.img_height) / 2);
	return scaled_img[starty:starty+params.img_height, startx:startx+params.img_width,:]

def preprocess(img):
	if args.pre == "crop":
		img = crop_image(img)
	else:
		img = cv2.resize(img, (params.img_width, params.img_height))
		# Convert to grayscale and readd channel dimension
	if params.img_channels == 1:
		img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
		img = np.reshape(img, (params.img_height, params.img_width, params.img_channels))
		img = img / 255.
	return img

def overlay_image(l_img, s_img, x_offset, y_offset):
	assert y_offset + s_img.shape[0] <= l_img.shape[0]
	assert x_offset + s_img.shape[1] <= l_img.shape[1]

	l_img = l_img.copy()
	
	for c in range(0, 3):
		l_img[y_offset:y_offset+s_img.shape[0],
		x_offset:x_offset+s_img.shape[1], c] = (
		s_img[:,:,c] * (s_img[:,:,3]/255.0) +
		l_img[y_offset:y_offset+s_img.shape[0],
		x_offset:x_offset+s_img.shape[1], c] * (1.0 - s_img[:,:,3]/255.0))
		return l_img

def angle_to_thrust(speed, theta):
	try:
		theta = ((theta + 180) % 360) - 180  # normalize value to [-180, 180)
		speed = min(max(0, speed), 100) # normalize value to [0, 100]
		v_a = speed * (45 - theta % 90) / 45 # falloff of main motor
		v_b = min(100, 2 * speed + v_a, 2 * speed - v_a) # compensation of other motor
		if theta < -90: return -v_b, -v_a
		if theta < 0:   return -v_a, v_b
		if theta < 90:  return v_b, v_a
		return [v_a, -v_b]
	except:
			logging.error("Couldn't calculate steering angle!")

##########################################################
# program begins
##########################################################

parser = argparse.ArgumentParser(description='Odyssey NNN Main Program')
parser.add_argument("-d", "--dnn", help="Enable DNN", action="store_true")
parser.add_argument("-t", "--throttle", help="throttle percent. [0-100]%", type=int, default=50)
parser.add_argument("--turnthresh", help="throttle percent. [0-30]degree", type=int, default=10)
parser.add_argument("-n", "--ncpu", help="number of cores to use.", type=int, default=2)
parser.add_argument("-f", "--hz", help="control frequnecy", type=int)
parser.add_argument("--fpvvideo", help="Take FPV video of DNN driving", action="store_true")
parser.add_argument("--use_tensorflow", help="use the full tensorflow instead of tflite", action="store_true")
parser.add_argument("--pre", help="preprocessing [resize|crop]", type=str, default="resize")
args = parser.parse_args()

if args.dnn:
	print("DNN is on!")
	USE_NETWORK = True
if args.throttle:
	print ("throttle = %d pct" % (args.throttle))
if args.turnthresh:
	args.turnthresh = args.turnthresh
	print ("turn angle threshold = %d degree\n" % (args.turnthresh))
if args.hz:
	period = 1.0/args.hz
	print("new period: ", period)
if args.fpvvideo:
	FPV_VIDEO = True
	print("FPV video of DNN driving is on")

print ("preprocessing:", args.pre)

##########################################################
# import car's DNN model
##########################################################
print ("Loading model: " + params.model_file)

print("use_tensorflow:", args.use_tensorflow)
if args.use_tensorflow:
	from tensorflow import keras
	model = keras.models.load_model(params.model_file+'.h5')
else:
	logging.warning("L bozo ur not using tflite. Using H5 instead...")
	from tensorflow import keras
	model = keras.models.load_model(params.model_file+'.h5')
	
	"""try:
			# Import TFLite interpreter from tflite_runtime package if it's available.
			from tflite_runtime.interpreter import Interpreter
			interpreter = Interpreter(params.model_file+'.tflite', num_threads=args.ncpu)
	except ImportError:
			# Import TFLMicro interpreter
			try:
					from tflite_micro_runtime.interpreter import Interpreter
					interpreter = Interpreter(params.model_file+'.tflite')
			except:
					# If all failed, fallback to use the TFLite interpreter from the full TF package.
					import tensorflow as tf
					interpreter = tf.lite.Interpreter(model_path=params.model_file+'.tflite', num_threads=args.ncpu)

	interpreter.allocate_tensors()
	input_index = interpreter.get_input_details()[0]["index"]
	output_index = interpreter.get_output_details()[0]["index"]"""

# initialize car modules
#actuator.init(args.throttle)
camera.init(res=CAMERA_RESOLUTION, fps=CAMERA_FPS, threading=USE_THREADING)
atexit.register(turn_off)

g = g_tick()
start_ts = time.time()

frame_arr = []
angle_arr = []

# startup signal
starup_signal(1, 0.2)

# enter main loop
while True:
	if USE_THREADING:
		time.sleep(next(g))
	frame = camera.read_frame()
	ts = time.time()

	if VIDEO_FEED == True:
		cv2.imshow('frame', frame)
		cv2.waitKey(1) & 0xFF

	# receive input (must be non blocking)
	ch = inputdev.read_single_event()

	if ch == ord('j'): # left
		angle = deg2rad(-30)
		move(BASE_SPEED - BASE_SPEED//2, BASE_SPEED)
		#actuator.left()
		print ("left")
	elif ch == ord('k'): # center
		angle = deg2rad(0)
		#actuator.center()
		print("center")
	elif ch == ord('l'): # right
		angle = deg2rad(30)
		#actuator.right()
		move(BASE_SPEED, BASE_SPEED - BASE_SPEED//2)
		print("right")
	elif ch == ord('a'):
		#actuator.ffw()
		move(BASE_SPEED, BASE_SPEED)
		print("accel")
	elif ch == ord('s'):
		#actuator.stop()
		off()
		print ("stop")
	elif ch == ord('z'):
		#actuator.rew()
		move(-BASE_SPEED, -BASE_SPEED)
		print("reverse")
	elif ch == ord('r'):
		print ("toggle record mode")
		RECORD_DATA = not RECORD_DATA
	elif ch == ord('t'):
		print ("toggle video mode")
		VIDEO_FEED = not VIDEO_FEED
	elif ch == ord('d'):
		print ("toggle DNN mode")
		USE_NETWORK = not USE_NETWORK
	elif ch == ord('q'):
		break
	elif USE_NETWORK == True:
		# 1. machine input
		img = preprocess(frame)
		img = np.expand_dims(img, axis=0).astype(np.float32)
		if args.use_tensorflow:
			angle = model.predict(img)[0]
		else:
			logging.warning("L bozo ur not using tflite. Using H5 instead...")
			angle = model.predict(img)[0]
			"""interpreter.set_tensor(input_index, img)
			interpreter.invoke()
			angle = interpreter.get_tensor(output_index)[0][0]"""

		degree = rad2deg(angle)
		if degree <= -args.turnthresh:
			actuator.left()
			print ("left (%d) by CPU" % (degree))
		elif degree < args.turnthresh and degree > -args.turnthresh:
			actuator.center()
			print ("center (%d) by CPU" % (degree))
		elif degree >= args.turnthresh:
			actuator.right()
			print ("right (%d) by CPU" % (degree))

	dur = time.time() - ts
	if dur > period:
		print("%.3f: took %d ms - deadline miss."
		% (ts - start_ts, int(dur * 1000)))
	else:
		print("%.3f: took %d ms" % (ts - start_ts, int(dur * 1000)))

	if RECORD_DATA == True and frame_id == 0:
		# create files for data recording
		keyfile = open(params.rec_csv_file, 'w+')
		keyfile.write("ts,frame,wheel\n") # ts (ms)
		try:
			fourcc = cv2.cv.CV_FOURCC(*'XVID')
		except AttributeError as e:
			fourcc = cv2.VideoWriter_fourcc(*'XVID')
			vidfile = cv2.VideoWriter(params.rec_vid_file, fourcc, CAMERA_FPS, CAMERA_RESOLUTION)

	if RECORD_DATA == True and frame is not None:
		# increase frame_id
		frame_id += 1

		# write input (angle)
		str = "{},{},{}\n".format(int(ts*1000), frame_id, angle)
		keyfile.write(str)

		if USE_NETWORK and FPV_VIDEO:
			textColor = (255,255,255)
			bgColor = (0,0,0)
			newImage = Image.new('RGBA', (100, 20), bgColor)
			drawer = ImageDraw.Draw(newImage)
			drawer.text((0, 0), "Frame #{}".format(frame_id), fill=textColor)
			drawer.text((0, 10), "Angle:{}".format(angle), fill=textColor)
			newImage = cv2.cvtColor(np.array(newImage), cv2.COLOR_BGR2RGBA)
			frame = overlay_image(frame, newImage, x_offset = 0, y_offset = 0)
			# write video stream
			vidfile.write(frame)
			#img_name = "cal_images/opencv_frame_{}.png".format(frame_id)
			#cv2.imwrite(img_name, frame)
			if frame_id >= 1000:
				print ("recorded 1000 frames")
				break
			print ("%.3f %d %.3f %d(ms)" % (ts, frame_id, angle, int((time.time() - ts)*1000)))

print("Finish!")
turn_off()