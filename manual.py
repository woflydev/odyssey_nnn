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
MAX_SPEED = 80

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

# takes in value of -90 to 90, with 0 being straight
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

startup_signal(1, 0.1)

current_angle = 0
current_speed = 0

try:
	while True:
		left = (ds.state.LY / 128 * 100) * LIMIT
		right = (ds.state.RY / 128 * 100) * LIMIT
		light = ds.state.L1 * 100 # ds.state.L2 ** 2 / (16384 / 25) # gradual control

		if ds.state.triangle == 1:
			current_speed += 10 if current_speed < MAX_SPEED else 0
			print("accelerate")
		elif ds.state.cross == 1:
			current_speed -= 10 if current_speed > 0 else 0
			print("decelerate")
		elif ds.state.circle == 1:
			current_angle += 6 if current_angle < 90 - 6 else 0
		elif ds.state.square == 1:
			current_angle -= 6 if current_angle > -90 + 6 else 0

		pwm = angle_to_thrust(current_speed, current_angle)
		pwm_left = int(pwm[0])
		pwm_right = int(pwm[1])

		if ds.state.R1 == 1:   # brake with R1
				left = 0
				right = 0
				print(f'Brake: [{left}, {right}]')

		if ds.state.R2 > 16:              # coast with R2
				left = 0
				right = 0
				print(f'Coast: [{left}, {right}]')
				off()

		if ds.state.L1 == 1:
			current_angle = 0

		if ds.state.L2 > 10:
			current_speed = 0
			current_angle = 0
		
		move(pwm_left, pwm_right)

		"""if ds.state.cross == 1:            # exit with cross
				left = 0
				right = 0
				print(f'[{left}, {right}]')
				off()
				print("Stopped.")
				quit()"""
		
		time.sleep(0.05)

		#print(f'[{left}, {right}]')
		#move(-left, -right)
		#drivePin(15, 0)

except KeyboardInterrupt:
	off()
	print("Keyboard Interrupt!")
	exit()