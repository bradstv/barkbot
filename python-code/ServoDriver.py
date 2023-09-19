import time
import math
import smbus

class Servo:
  __SUBADR1            = 0x02
  __SUBADR2            = 0x03
  __SUBADR3            = 0x04
  __MODE1              = 0x00
  __PRESCALE           = 0xFE
  __LED0_ON_L          = 0x06
  __LED0_ON_H          = 0x07
  __LED0_OFF_L         = 0x08
  __LED0_OFF_H         = 0x09
  __ALLLED_ON_L        = 0xFA
  __ALLLED_ON_H        = 0xFB
  __ALLLED_OFF_L       = 0xFC
  __ALLLED_OFF_H       = 0xFD
  MAX_PW = 2500
  MIN_PW = 500
  _freq = 50

  def __init__(self, address=0x40, freq=50,debug=False):
    self.bus = smbus.SMBus(1)
    self.address = address
    self.debug = debug
    self.last_angle = [0, 0, 0]
    if (self.debug):
      print("Reseting PCA9685")
    self.write(self.__MODE1, 0x00)
    self.setPWMFreq(freq)
    self.hasObject = False
    self.angle(0, -30)
    time.sleep(0.2)
    self.angle(1, 45)
    time.sleep(0.2)
    self.angle(2, 80)
	
  def write(self, reg, value):
    "Writes an 8-bit value to the specified register/address"
    self.bus.write_byte_data(self.address, reg, value)
    if (self.debug):
      print("I2C: Write 0x%02X to register 0x%02X" % (value, reg))
	  
  def read(self, reg):
    "Read an unsigned byte from the I2C device"
    result = self.bus.read_byte_data(self.address, reg)
    if (self.debug):
      print("I2C: Device 0x%02X returned 0x%02X from reg 0x%02X" % (self.address, result & 0xFF, reg))
    return result
	
  def setPWMFreq(self, freq):
    "Sets the PWM frequency"
    prescaleval = 25000000.0    # 25MHz
    prescaleval /= 4096.0       # 12-bit
    prescaleval /= float(freq)
    prescaleval -= 1.0
    if (self.debug):
      print("Setting PWM frequency to %d Hz" % freq)
      print("Estimated pre-scale: %d" % prescaleval)
    prescale = math.floor(prescaleval + 0.5)
    if (self.debug):
      print("Final pre-scale: %d" % prescale)

    oldmode = self.read(self.__MODE1);
    newmode = (oldmode & 0x7F) | 0x10        # sleep
    self.write(self.__MODE1, newmode)        # go to sleep
    self.write(self.__PRESCALE, int(math.floor(prescale)))
    self.write(self.__MODE1, oldmode)
    time.sleep(0.005)
    self.write(self.__MODE1, oldmode | 0x80)

  def setPWM(self, channel, on, off):
    "Sets a single PWM channel"
    self.write(self.__LED0_ON_L+4*channel, on & 0xFF)
    self.write(self.__LED0_ON_H+4*channel, on >> 8)
    self.write(self.__LED0_OFF_L+4*channel, off & 0xFF)
    self.write(self.__LED0_OFF_H+4*channel, off >> 8)
    if (self.debug):
      print("channel: %d  LED_ON: %d LED_OFF: %d" % (channel,on,off))
	  
  def setServoPulse(self, channel, pulse):
    "Sets the Servo Pulse,The PWM frequency must be 50HZ"
    pulse = pulse*4096/20000        #PWM frequency is 50HZ,the period is 20000us
    self.setPWM(channel, 0, int(pulse))
  
  def map(self, x, in_min, in_max, out_min, out_max): #map angle value to pwm value
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
    
  def angle(self, channel, angle):
    if not (isinstance(angle, int) or isinstance(angle, float)):
        raise ValueError("Angle value should be int or float value, not %s"%type(angle))
    if angle < -90:
        angle = -90
    if angle > 90:
        angle = 90
    self.last_angle[channel] = angle
    High_level_time = self.map(angle, -90, 90, self.MIN_PW, self.MAX_PW)
    self.setServoPulse(channel, High_level_time)
    
  def moveto(self, channel, angle, speed):
    last_angle = self.last_angle[channel]
    if (self.debug):
      print(self.last_angle)
      print("moving channel :" + str(channel))
      print("last angle: " + str(last_angle))
    
    steps = 1
    if angle < last_angle:
      steps = -1

    for i in range(last_angle, angle, steps):
      self.angle(channel, i + steps)
      time.sleep(speed)
      
  def doPickup(self):
    self.moveto(2, 0, 0.01)
    self.moveto(1, 0, 0.01)
    self.moveto(0, 35, 0.01)
    self.moveto(1, -48, 0.01)
    self.moveto(0, 70, 0.01)
    self.moveto(2, 80, 0.01)
    time.sleep(1)
    self.moveto(0, 35, 0.01)
    self.moveto(1, 0, 0.01)
    self.moveto(0, 0, 0.01)
    self.moveto(1, 45, 0.01)
    self.moveto(0, -30, 0.01)
    
  def doDrop(self):
    self.moveto(0, -5, 0.01)
    self.moveto(1, 25, 0.01)
    self.moveto(0, 10, 0.01)
    time.sleep(1)
    self.moveto(2, 0, 0.01)
    time.sleep(1)
    self.moveto(0, -30, 0.01)
    self.moveto(1, 45, 0.01)
    self.moveto(2, 80, 0.01)