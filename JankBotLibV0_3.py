"""
JankBotLib V0.3

By: NotAWildernessExplorer

"""
import time 
import digitalio
import board
import pwmio


class Wheel:
    """
    board.pin: wheel_GS_pin      -> Gear Select for wheel (high-> Drive, low-> reverse)
    board.pin: wheel_PWM_pin     -> Vroom Vroom controls for wheel
    int:       pwm_freq          -> Set the pwm frequency
    bool:      training_wheels   -> True-> max pwm at 5%; False->wide open
    float:     tw_percent        -> Traning wheels percent
    """
    def __init__(self,wheel_GS_pin,wheel_PWM_pin,pwm_freq = 1000,training_wheels = False,tw_percent = 0.05):
        
        self.wheel_PWM = pwmio.PWMOut(wheel_PWM_pin, frequency=pwm_freq, duty_cycle=0)       # init the PWM for Right wheel
        self.wheel_GS = digitalio.DigitalInOut(wheel_GS_pin)                                 # init the Gear select pin
        self.wheel_GS.direction = digitalio.Direction.OUTPUT                                 # Set to output    
        
        self.max_PWM = 65535 if not training_wheels else int(65535*tw_percent)                     # Set the max motor speed
        self.dir_dic = {"F": True,"R":False}                                                 # Just a dictonary so we can pass keys, might change later


    def update_motor(self,direction = "F",percent = 0.0):
        """ 
        Updates the pwm signal being set to a motor:

        obj:    self           -> Wheel object
        str:    direction      -> String "F" = Forward; "R" = Reverse
        float:  percent        -> pecent [0,100] of max pwm
        
        """
        # For changing directions
        if self.wheel_GS.value != self.dir_dic[direction]:

            self.wheel_PWM.duty_cycle         = int(0)                                # Turn off the motor
            #time.sleep(0.001)                                               # Let the motor chill for a 10ms
            self.wheel_GS.value     = self.dir_dic[direction]               # Set the new direction
            self.wheel_PWM.duty_cycle   = int(percent/100* self.max_PWM)    # set the wheel speed
            return None
        
        self.wheel_PWM.duty_cycle = int(percent/100* self.max_PWM)              # set the new wheel speed



        
class LORA:
    
    def __init__(self,SPI_BUSSY,RESET_PIN,CS_PIN):
        import adafruit_rfm9x
        import struct
        self.LORA_RESET_PIN   = digitalio.DigitalInOut(RESET_PIN)    # GP8 for Telm-Board
        self.LORA_CS_PIN      = digitalio.DigitalInOut(CS_PIN)       # GP1 for Telm-Board
        self.RADIO_FREQ_MHZ   = 915.0                                # Frequency of the radio in Mhz. 
        self.test = struct.pack('<i',int(1))
        self.rfm9x = adafruit_rfm9x.RFM9x(SPI_BUSSY, self.LORA_CS_PIN, self.LORA_RESET_PIN, self.RADIO_FREQ_MHZ)    # Initialze RFM radio
        self.rfm9x.tx_power = 23                                                                                    # Change the power
        
        print("Radio Has Been Set")

 
    def decode_lora_packet(self,packet,index):
        packet_text = str(packet, "utf-8")
        right_text = packet_text.split('\t')[index].split(' ')
        right_text[2] = float(right_text[2])
        return right_text
    
    def encode_lora_packet(self):
        pass

    def get_message(self):
        self.packet = self.rfm9x.receive(timeout=5.0)
        if self.packet is not None:
            # return self.decode_lora_packet(self.packet,0),self.decode_lora_packet(self.packet,1)
            return struct.unpack('<ii',self.packet)          
        return (None,None)
    


class Joystick:
    
    def __init__(self,board_pin):
        from analogio import AnalogIn
        self.joy_pin = AnalogIn(board_pin)                                   # Set the pin to be and analog
        self.adc_res     = 2**16                                             # resolution of the adc
        self.dead_zone   = 0.1                                               # percent (0,1) of the signal that outputs zero
        self.joy_val     = 0.0
        self.history_len = 10
        self.val_history = [0]*self.history_len

    def get_joy_pos(self):
        '''returns the position of the joystick on a scale of (-1,1)'''

        self.joy_val = (self.joy_pin.value - self.adc_res/2.0) / (self.adc_res/2.0)     # read the pin and convert to (-1,1) scaleing 
        
        ## check if in deadzone and output accordingly
        if   abs(self.joy_val) <= self.dead_zone:
            return 0.0
        elif abs(self.joy_val) >  self.dead_zone:
            return self.joy_val
        raise ValueError("wead wrong wale")


    def read_joy(self):
        '''keeps a history '''
        self.val_history.pop(0)
        self.val_history.append(self.get_joy_pos())
        return sum(self.val_history)/self.history_len
    
def joysick_to_PWM(joy_direction,joy_throttle,bias):

    def keep_it_100(value):
        if abs(value) < 100:
            return int(value)
        if abs(value) >=100:
            return int(value/abs(value) * 100)
    
    
    PWM_Left,PWM_Right = joy_throttle,joy_throttle
    scale = joy_direction + bias

    '''Scales between [0,1]'''
    PWM_Left  = PWM_Left  * (1+scale)
    PWM_Right = PWM_Right * (1-scale)
    return keep_it_100(PWM_Left*100),keep_it_100(PWM_Right*100)