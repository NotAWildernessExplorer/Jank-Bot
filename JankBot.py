'''
Jank-bot motor controler code
Writen:     12/30/2023      NotAWildernessExplorer


Ment to be used with the old telm boards from the 2023 solar car race
'''
import board
import busio
import time
import struct
from JankBotLib import Wheel,LORA

## Begin the jank
time.sleep(2.0)
print("Let the Jank begin!")


# Initalize the SPI bus on the RP2040
# NOTE: Theses pins constant for all CAN-Pico Boards... DO NOT TOUCH
spi = busio.SPI(board.GP2, board.GP3, board.GP4)


# Initalize the lora
LORA_RESET_PIN   = board.GP8                                # GP8 for Telm-Board
LORA_CS_PIN      = board.GP1                                # GP1 for Telm-Board
lora             = LORA(spi,LORA_RESET_PIN,LORA_CS_PIN)     # Setup the lora


## Set the pins
wheel_left_GS_pin  = board.GP20           # GS -> Gear Select (high-> Drive, low-> reverse)
wheel_left_PWM_pin = board.GP19         # PWM-> Vroom Vroom controls 
wheel_right_GS_pin  = board.A0        # GS -> Gear Select (high-> Drive, low-> reverse)
wheel_right_PWM_pin = board.GP10        # PWM-> Vroom Vroom controls 

## initalize both wheels and set the pwm to zero
wheel_left  = Wheel(wheel_left_GS_pin,wheel_left_PWM_pin,training_wheels= True,tw_percent = 0.25)
wheel_right = Wheel(wheel_right_GS_pin,wheel_right_PWM_pin,training_wheels= True,tw_percent = 0.25)
wheel_right.update_motor("F",0.0)
wheel_left.update_motor("F",0.0)


## Function that takes the sign and returns the direction of wheel
def sign_to_dir(value):
    if value >=0:
        return "F"
    else:
        return "R"

## initalize the timeout clock 
last_rec_time = time.monotonic_ns()

while True:
    
    packet = lora.rfm9x.receive(timeout=5.0)    # Recieve lora packet

    ## If we get a packet
    if packet is not None:

        
        left_message,right_message = struct.unpack('<ii',packet)    # Unpack the message
        
        dirr_right  = sign_to_dir(right_message)                    # Gather the direction for right
        dirr_left   = sign_to_dir(-1.0*left_message)                # Gather the direction for left, note the -1.0 is bc the motor is backwards

        ##Update motors
        wheel_right.update_motor(dirr_right,abs(right_message))
        wheel_left.update_motor(dirr_left,abs(left_message))


        
        last_rec_time = time.monotonic_ns()

        ## Print out to terminal there commands
        print(f"{dirr_left}\t{left_message}\t{dirr_right}\t{right_message}")
    else:
        print("Waiting...")
    ## Shut off both wheels if last message was recieved over a 1.0s ago
    if time.monotonic_ns() - last_rec_time > 1000000000:
        wheel_right.update_motor("F",0.0)
        wheel_left.update_motor( "F",0.0)    
