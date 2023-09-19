import RPi.GPIO as GPIO
import time
from threading import Thread

class Motor:
	def __init__(self, IN1 = 16, IN2 = 18, IN3 = 13, IN4 = 15, ENA = 12, ENB = 33, disable=False):
		self.IN1 = IN1
		self.IN2 = IN2
		self.IN3 = IN3
		self.IN4 = IN4
		self.ENA = ENA
		self.ENB = ENB
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(self.IN1, GPIO.OUT)
		GPIO.setup(self.IN2, GPIO.OUT)
		GPIO.setup(self.IN3, GPIO.OUT)
		GPIO.setup(self.IN4, GPIO.OUT)
		GPIO.setup(self.ENA, GPIO.OUT)
		GPIO.setup(self.ENB, GPIO.OUT)
		self.rightmotor = GPIO.PWM(self.ENA,1000)	
		self.leftmotor = GPIO.PWM(self.ENB,1000)	
		self.rightmotor.start(0)
		self.leftmotor.start(0)
		self.isMoving = False
		self.disable=disable
		
	def go_foward(self, speed):
		if self.disable:
			return
		GPIO.output(self.IN1,False)
		GPIO.output(self.IN2,True)
		GPIO.output(self.IN3,False) 
		GPIO.output(self.IN4,True)
		self.rightmotor.ChangeDutyCycle(speed)
		self.leftmotor.ChangeDutyCycle(speed)
		self.isMoving = True
	
	def go_backwards(self, speed):
		if self.disable:
			return
		GPIO.output(self.IN1,True)
		GPIO.output(self.IN2,False)
		GPIO.output(self.IN3,True)
		GPIO.output(self.IN4,False)
		self.rightmotor.ChangeDutyCycle(speed)
		self.leftmotor.ChangeDutyCycle(speed)
		self.isMoving = True
		
	def turn_right(self, speed, both_wheels=True):
		if self.disable:
			return
		if both_wheels:	
			GPIO.output(self.IN1,True)
			GPIO.output(self.IN2,False)
			GPIO.output(self.IN3,False)
			GPIO.output(self.IN4,True) 
			self.leftmotor.ChangeDutyCycle(speed)
			self.rightmotor.ChangeDutyCycle(speed)
		else:
			GPIO.output(self.IN1,False)
			GPIO.output(self.IN2,False)
			GPIO.output(self.IN3,False)
			GPIO.output(self.IN4,True)
			self.leftmotor.ChangeDutyCycle(speed)
		self.isMoving = True
		
	def turn_left(self, speed, both_wheels=True):
		if self.disable:
			return
		if both_wheels:
			GPIO.output(self.IN1,False)
			GPIO.output(self.IN2,True)
			GPIO.output(self.IN3,True)
			GPIO.output(self.IN4,False)
			self.rightmotor.ChangeDutyCycle(speed)
			self.leftmotor.ChangeDutyCycle(speed)
		else:
			GPIO.output(self.IN1,False)
			GPIO.output(self.IN2,True)
			GPIO.output(self.IN4,False)
			GPIO.output(self.IN3,False)
			self.rightmotor.ChangeDutyCycle(speed)
		self.isMoving = True
		
	def stop(self):
		#print("Stopping motor")
		GPIO.output(self.IN2,False)
		GPIO.output(self.IN1,False)
		GPIO.output(self.IN3,False)
		GPIO.output(self.IN4,False)
		self.isMoving = False
		
	def cleanup(self):
		self.stop()
		GPIO.cleanup()
