try:
    from board import SCL, SDA
    import busio
    from adafruit_pca9685 import PCA9685
except ImportError:
    raise ImportError("Motor driver not initialized. Only runs on Linux!")

from time import sleep
#from math import abs

PWM_FREQ = 1000      # (Hz) max is 1.5 kHz
MAP_CONST = 65535 / 120   # 65535 / 120 to limit speed below 100% duty cycle
HALF_WIDTH = 0.1          # Half of the width of droid, in metres
MAX_CENT_ACC = 30000 # Maximum "centripetal acceleration" the robot is allowed to undergo. UNITS ARE DODGY, MUST BE DETERMIEND BY EXPERIMENTATION
MAX_SPEED = MAP_CONST * 100 / 65535  # (percent) max speed of motors

i2c_bus = busio.I2C(SCL, SDA)

# create PCA9685 class instance.
pca = PCA9685(i2c_bus)
pca.frequency = PWM_FREQ

# duty_cycle is 16 bits to match other PWM objects
# but the PCA9685 will only actually give 12 bits of resolution.
# 65535 is the maximum value.

pca.channels[0].duty_cycle = 0
pca.channels[1].duty_cycle = 0
pca.channels[2].duty_cycle = 0
pca.channels[3].duty_cycle = 0

motorLA = pca.channels[2]
motorLB = pca.channels[3]
motorRA = pca.channels[0]
motorRB = pca.channels[1]

motorENL = pca.channels[4]
motorENR = pca.channels[5]

print("Motor driver initialized. \n path: utils\motor_lib\driver.py \n PWM frequency: " + str(PWM_FREQ) + "Hz \n Max speed: " + str(MAX_SPEED) + "%")

# Path: utils\motor_lib\driver.py
# off/coast/stop are the same
def off():
    # Enable pins are low during off() to coast
    motorENL.duty_cycle = 0
    motorENR.duty_cycle = 0

    motorLA.duty_cycle = 0
    motorLB.duty_cycle = 0
    motorRA.duty_cycle = 0
    motorRB.duty_cycle = 0

def stop():
    off()
    
def coast():
    off()

def brake():
    off()
    motorLA.duty_cycle = 0
    motorLB.duty_cycle = 0
    motorRA.duty_cycle = 0
    motorRB.duty_cycle = 0
    # Enable pins are high during brake() to brake
    motorENL.duty_cycle = 65535
    motorENR.duty_cycle = 65535

# brakes after 1.5s of coasting
def ebrake():
    off()
    sleep(1.5) # sleep(1.5)
    motorLA.duty_cycle = 65535
    motorLB.duty_cycle = 65535
    motorRA.duty_cycle = 65535
    motorRB.duty_cycle = 65535

# forward function
def fwd(speed, timeout=0):
    motorLA.duty_cycle = int(speed * MAP_CONST)
    motorLB.duty_cycle = 0
    motorRA.duty_cycle = int(speed * MAP_CONST)
    motorRB.duty_cycle = 0
    motorENL.duty_cycle = 65535
    motorENR.duty_cycle = 65535
    if timeout > 0:
        sleep(timeout / 1000)
        off()

# reverse function
def rev(speed, timeout=0):
    motorLA.duty_cycle = 0
    motorLB.duty_cycle = int(speed * MAP_CONST)
    motorRA.duty_cycle = 0
    motorRB.duty_cycle = int(speed * MAP_CONST)
    motorENL.duty_cycle = 65535
    motorENR.duty_cycle = 65535
    if timeout > 0:
        sleep(timeout / 1000)
        off()

# Write motor values for a turn, where a positive radius denotes a right turn (think +x), and negatvie radius defines left turn
def turn(speed: float, radius: float, timeout=0):
    r = abs(radius)
    if(speed < 0 or speed > 100):
        raise Exception(f"[MOTOR]: Invalid turn speed {speed}")
    if( r == 0 or speed * speed / r > MAX_CENT_ACC):
        print("[MOTOR]: Ignored attempt to turn at speed {speed} and radius {r} due to potential slipping.")
        return # Should I raise an exception instead?
    omega = speed / r
    if(radius > 0):
        move(omega * (r + HALF_WIDTH), omega * (r - HALF_WIDTH), timeout)
    elif(radius == 0):
        move(omega * (r - HALF_WIDTH), omega * (r + HALF_WIDTH), timeout)

# input -100 to 100 left and right sides
def move(LIN, RIN, timeout=0):
    LIN = round(LIN / 5) * 5
    RIN = round(RIN / 5) * 5
    L = int(LIN * MAP_CONST)  # map values to 0-65535
    R = int(RIN * MAP_CONST)
    #print(L, R)
    if L == 0 and R == 0:
        off()
        brake()
    else:
        #print(L, R)
        if L > 0:
            motorLA.duty_cycle = L
            motorLB.duty_cycle = 0
        else:
            motorLA.duty_cycle = 0
            motorLB.duty_cycle = -L
        if R > 0:
            motorRA.duty_cycle = R
            motorRB.duty_cycle = 0
        else:
            motorRA.duty_cycle = 0
            motorRB.duty_cycle = -R
    
    motorENL.duty_cycle = 65535
    motorENR.duty_cycle = 65535
    if timeout > 0:
        sleep(timeout / 1000)
        off()

# Drive pins other than motor pins
def drivePin(pin, val):
    if pin == 0 or pin == 1 or pin == 2 or pin == 3:
        raise Exception(f"Pin {pin} is used for motors.")
    else:
        pca.channels[pin].duty_cycle = int(val / 100 * 65535)
        print(f"Pin {pin} set to {val}%")