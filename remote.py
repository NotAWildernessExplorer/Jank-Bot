'''
Jankbot_remote.py sends commands to jankbot
Written: 01/02/2024      By: NotAWildernessExplorer

Note: rename to either code.py or main.py when saving to rp2040
'''
import board
import busio
import time
import struct
from JankBotLib import LORA,Joystick,joysick_to_PWM


# Initalize the SPI bus on the RP2040
spi = busio.SPI(board.GP18, board.GP19, board.GP16)


## Initalize the lora
LORA_RESET_PIN   = board.GP20                               # GP8 for Telm-Board
LORA_CS_PIN      = board.GP21                               # GP1 for Telm-Board
lora             = LORA(spi,LORA_RESET_PIN,LORA_CS_PIN)     # Turn on LoRa module


## Initalize the joysicks
joy_x = Joystick(board.A0)          # Joystick dirrection for the left wheel
joy_y = Joystick(board.A1)          # Joystick dirrection for the right wheel


## set the 'initial send'
last_send = time.monotonic_ns()

while True:

    ## only send a message every 100ms
    while time.monotonic_ns()  - last_send > 100000000:
        PWML,PWMR  = joysick_to_PWM(joy_x.read_joy(),joy_y.read_joy(),0.0)      # read the joysticks

        msg_data = struct.pack('<ii',PWML,PWMR)                                 # Pack the signals
        sucuess  = lora.rfm9x.send(msg_data)                                    # Send the message

        last_send = time.monotonic_ns()                                         # Reset message timer
        print(f"Last Send: {sucuess}\t{PWML}\t{PWMR}")                          # Print last message stats                        
