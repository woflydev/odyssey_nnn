from pydualsense import *
from utils.motor_lib.driver import *
import params as params
import time
import logging
import cv2
import numpy as np
import utils.camera.webcam as camera
# requires libhidapi-dev

#---------------------#
# Camera Config       #
#---------------------#
CAMERA_FPS = 30
CAMERA_RESOLUTION = (640, 360) #width then height
VIDEO_FEED = False
USE_THREADING = True
RECORD_DATA = True
RECORD_DATA = False
MAX_SPEED = 95

#---------------------#
# System Variables	  #
#---------------------#
frame_id = 0
angle = 0.0
period = 0.05 # sec (=50ms)

#---------------------#
# Console Logging	  #
#---------------------#
logging.basicConfig(level=logging.INFO)

camera.init(res=CAMERA_RESOLUTION, fps=CAMERA_FPS, threading=USE_THREADING)

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

# takes in value of -90 to 90, with 0 being straight (unlike sid lol)
def angle_to_thrust(speed, theta):
	try:
		theta = ((theta + 180) % 360) - 180  # normalize value to [-180, 180)
		speed = min(max(0, speed), 100) # normalize value to [0, 100]
		v_a = speed * (45 - theta % 90) / 45 # falloff of main motor
		v_b = min(100, 2 * speed + v_a, 2 * speed - v_a) # compensation of other motor
		if theta < -90: return -v_b, -v_a
		if theta < 0:   return -v_a, v_b
		if theta < 90:  return v_b, v_a
		return int([v_a, -v_b])
	except:
		logging.error(f"Couldn't calculate - SPEED: {speed}, ANGLE: {theta}")

ds = pydualsense() 		# open controller
ds.init() 			# initialize controller

ds.light.setColorI(0,255,0) 	# set touchpad color to red
ds.triggerL.setMode(TriggerModes.Rigid)
ds.triggerR.setMode(TriggerModes.Pulse)
ds.conType.BT = False 		# set connection type to bluetooth

current_angle = 0
current_speed = 0


#gst_out = f"appsrc ! video/x-raw,format=BGR ! queue ! videoconvert ! video/x-raw,format=BGRx ! nvvidconv ! omxh264enc ! h264parse ! qtmux ! filesink location=video_output.mp4"
#out = cv2.VideoWriter(gst_out, cv2.CAP_GSTREAMER, CAMERA_FPS, CAMERA_RESOLUTION)

# WITH THIS (0x7634706d / mp4v) 
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
# THIS WORKS 
out = cv2.VideoWriter("video_output.mp4", fourcc, float(CAMERA_FPS), CAMERA_RESOLUTION, True)

startup_signal(4, 0.1)

try:
	while True:
		ts = time.time()
		frame = camera.read_frame()
		#cv2.imwrite("webcam.test.png", frame)

		# ----- MOTORS ----- #  
		if ds.state.triangle == 1:
			current_speed += 10 if current_speed < MAX_SPEED else 0
			print(f"Speed: {current_speed}, Angle: {current_angle}")
		elif ds.state.cross == 1:
			current_speed -= 10 if current_speed > 0 else 0
			print(f"Speed: {current_speed}, Angle: {current_angle}")
		elif ds.state.circle == 1:
			current_angle += 3 if current_angle < 40 - 3 else 0 # 40 seems to be the optimal turning speed angle
			print(f"Speed: {current_speed}, Angle: {current_angle}")
		elif ds.state.square == 1:
			current_angle -= 3 if current_angle > -40 + 3 else 0 # see above
			print(f"Speed: {current_speed}, Angle: {current_angle}")

		pwm = angle_to_thrust(current_speed, current_angle)
		pwm_left = int(pwm[0])
		pwm_right = int(pwm[1])

		if ds.state.L1 == 1:
			current_angle = 0
			print(f"Speed: {current_speed}, Angle: {current_angle}")

		if ds.state.L2 > 10:
			current_speed = 0
			current_angle = 0
			print(f"Speed: {current_speed}, Angle: {current_angle}")
		
		if ds.state.DpadUp == 1:
			drivePin(15, 100)
			print("Lights on!")
		
		if ds.state.DpadDown == 1:
			drivePin(15, 0)
			print("Lights off!")
		
		if ds.state.DpadLeft == 1:
			RECORD_DATA = True
		if ds.state.DpadRight == 1:
			RECORD_DATA = False

		move(pwm_left, pwm_right)

		# must have delay or the robot receives too many pwm inputs
		time.sleep(0.07)

		if RECORD_DATA == True and frame_id == 0:
			# create files for data recording
			keyfile = open(params.rec_csv_file, 'w+')
			keyfile.write("ts,frame,wheel\n") # ts (ms)

			fourcc = cv2.VideoWriter_fourcc(*'mp4v')
			vidfile = cv2.VideoWriter(params.rec_vid_file, fourcc, float(CAMERA_FPS), CAMERA_RESOLUTION, True)

		if RECORD_DATA == True and frame is not None:
			# increase frame_id
			frame_id += 1

			# write input (angle)
			str = "{},{},{}\n".format(int(ts * 1000), frame_id, current_angle)
			keyfile.write(str)

			frame = camera.read_frame()
			# write video stream
			vidfile.write(frame)
			#img_name = "cal_images/opencv_frame_{}.png".format(frame_id)
			#cv2.imwrite(img_name, frame)
			if frame_id >= 1000:
				print ("recorded 1000 frames")
				break
			print("%.3f %d %.3f %d(ms)" % (ts, frame_id, current_angle, int((time.time() - ts)*1000)))

except:
	off()
	camera.stop()
	print("Interrupt! Immediate motor cutoff engaged!")
	exit(0)