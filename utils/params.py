#!/usr/bin/env python
##########################################################
# camera module selection
#   "camera-webcam" "camera-null"
##########################################################
camera="utils.camera.webcam_pc"

##########################################################
# actuator selection
#   "actuator-drv8835", "actuator-adafruit_hat"
#   "actuator-null", "driver"
##########################################################
actuator="lib.motor_lib.actuator-drv8835"

##########################################################
# intputdev selection
#   "input-kbd", "input-joystick", "input-web"
##########################################################
inputdev="keyboard"

##########################################################
# input config 
##########################################################
img_width = 200
img_height = 66
img_channels = 3

##########################################################
# model selection
#   "model_large"   <-- nvidia dave-2 model
##########################################################
model_name = "model_large"
#model_file = "data/models/{}-{}x{}x{}".format(model_name[6:], img_width, img_height, img_channels)
model_file = "data/models/ver1"

##########################################################
# recording config 
##########################################################
rec_vid_file="out-video"
rec_csv_file="out-key"