import serial
import time

class Ultrasonic:
	def __init__(self):
		self.ser = serial.Serial('/dev/ttyUSB0', 9600, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE, 0.1, False, False, False)
		self.last_received = ''
		self.buffer_string = ''
				
	def receiveUltra(self): #receives lastest ultra values from serial 
		self.buffer_string = self.buffer_string + self.ser.read(self.ser.inWaiting()).decode()
		if '\n' in self.buffer_string:
			lines = self.buffer_string.split('\n')
			self.last_received = lines[-2].split()
			self.buffer_string = lines[-1]
				
	def setPins(self, TRIG, ECHO):
		string = "init " + str(TRIG) + " " + str(ECHO) + "\n"
		self.ser.write(string.encode())
		
	def getValue(self, index):
		try: #try to get value of specific ultra, if errors then return 0
			value = int(self.last_received[index])
			return value
		except:
			return 0
	
	def UltraAvoidanceSetup(self):
		self.setPins(2, 3) 
		time.sleep(0.1) #add waits to avoid ultras from being set to wrong pins
		self.setPins(4, 5)
		time.sleep(0.1)
		self.setPins(6, 7)
		time.sleep(0.1)
		self.setPins(8, 9)
		time.sleep(0.1)
		self.ser.write(b"start\n")
	
	def stop(self):
		self.ser.write(b"stop\n")
		
	def cleanup(self):
		self.ser.write(b"stop\n")
		self.ser.close()
			
