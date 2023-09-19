from MotorController import Motor
from ServoDriver import Servo
from UltraSerial import Ultrasonic
from LCDDriver import LCD
from Object_Detect import ObjectDetect
from threading import Thread
import cv2
import time

class BarkBot:
    def __init__(self, show_fps=False, show_gui=False, min_conf=0.75, disable_motors=False):
        self.lcd = LCD(0x27)
        self.lcd.lcd_clear()
        self.lcd.lcd_display_string("BarkBot", 1)
        self.lcd.lcd_display_string("by Brad Alvarez", 2)
        time.sleep(1) #add waits for setup so PI doesn't crash due to overcurrent
        self.arm = Servo()
        time.sleep(1)
        self.car = Motor(disable=disable_motors)
        time.sleep(1)
        self.objdetect = ObjectDetect(show_gui=show_gui, min_conf_threshold=min_conf, threads=3)
        time.sleep(1)
        self.ultra = Ultrasonic()
        self.ultra.UltraAvoidanceSetup()
        self.F_ultra_range = 190
        self.FR_ultra_range = 140
        self.FL_ultra_range = 140
        self.B_ultra_range = 50
        self.mode = ""
        self.pickup_thread = False
        self.drop_thread = False
        self.search_thread = False
        self.backwards_thread = False
        self.writing_to_display = False
        self.deteced_ultra = False
        self.armHasObject = False
        self.start_right = True
        self.doSearch = True
        self.doCleanup = False
        self.searchCount = 0
        self.show_fps = show_fps
        if show_fps:
            self.frame_rate_calc = 1
            self.freq = cv2.getTickFrequency()
    
    def getSpeedforDist(self, distance):
        if distance < 20:
            return 50
        if distance < 15:
            return 45
        return 55
            
    def inRange(self, var, negval, posval):
        if var > negval and var < posval:
            return True
        return False
        
    def foundObject(self):
        if self.pickup_thread or self.objdetect.found_objects:
            return True
        return False

    def foundBin(self):
        if self.objdetect.found_bins or self.drop_thread:
            return True  
        return False
        
    def setMode(self, mode_string):
        if self.mode != mode_string and not self.writing_to_display:
            self.mode = mode_string
            self.writing_to_display = True
            Thread(target=self.writeLCD,args=(mode_string,)).start()

    def writeLCD(self, string):
        self.lcd.lcd_clear()
        self.lcd.lcd_display_string("BarkBot", 1)
        self.lcd.lcd_display_string(string, 2)
        self.writing_to_display = False
        
    def checkUltras(self):
        if self.ultra.getValue(1) < self.F_ultra_range:
            self.deteced_ultra = True
        elif self.ultra.getValue(3) < self.B_ultra_range:
            self.deteced_ultra = True
        elif self.ultra.getValue(0) < self.FR_ultra_range:
            self.deteced_ultra = True
            self.start_right = False
        elif self.ultra.getValue(2) < self.FL_ultra_range:
            self.deteced_ultra = True
            self.start_right = True
        else:
            self.deteced_ultra = False
            
    def checkIfPickupRange(self):
        time.sleep(1)
        self.setMode("Found Toy")
        
        while self.objdetect.found_objects and (not self.inRange(self.objdetect.found_objects[0][2], -30, 30)): #x_error check
            if self.objdetect.found_objects[0][2] > 0:
                self.car.turn_right(50, both_wheels=False)
                time.sleep(0.18)
                self.car.stop()
               
            elif self.objdetect.found_objects[0][2] < 0:
                self.car.turn_left(50, both_wheels=False)
                time.sleep(0.18)
                self.car.stop()
            time.sleep(0.5)
                
        time.sleep(0.5)
                
        while self.objdetect.found_objects and (not self.inRange(self.objdetect.found_objects[0][1], 6.0, 6.5)): #distance check
            if self.objdetect.found_objects[0][1] <= 6.0:
                self.car.go_backwards(45)
                time.sleep(0.10)
                self.car.stop()
                
            elif self.objdetect.found_objects[0][1] >= 6.5:
                self.car.go_foward(45)
                time.sleep(0.13)
                self.car.stop()
            time.sleep(0.5)
            
        time.sleep(0.5)
        
        if self.objdetect.found_objects and self.inRange(self.objdetect.found_objects[0][2], -30, 30) and self.inRange(self.objdetect.found_objects[0][1], 6.0, 6.5):
            self.setMode("Picking Up Toy")
            self.arm.doPickup()
            self.armHasObject = True
            self.setSearch()
        self.pickup_thread = False
        
    def checkIfDropRange(self):
        time.sleep(1)
        self.setMode("Found Bin")
        
        while self.objdetect.found_bins and (not self.inRange(self.objdetect.found_bins[0][2], -30, 30)): #x_error check
            if self.objdetect.found_bins[0][2] > 0:
                self.car.turn_right(50, both_wheels=False)
                time.sleep(0.18)
                self.car.stop()
               
            elif self.objdetect.found_bins[0][2] < 0:
                self.car.turn_left(50, both_wheels=False)
                time.sleep(0.18)
                self.car.stop()
            time.sleep(0.5)
                
        self.car.stop()
        time.sleep(1)
        
        if self.objdetect.found_bins and self.inRange(self.objdetect.found_bins[0][2], -30, 30):
            while not self.ultra.getValue(1) < 90: #distance check
                self.car.go_foward(45)
            
            self.car.stop()
            time.sleep(1)
            
            self.setMode("Dropping Toy")
            self.arm.doDrop()
            self.armHasObject = False
            
        self.drop_thread = False
        
    def checkifFoundObject(self):
        if self.objdetect.found_objects and not self.pickup_thread:
            self.setMode("Found Toy")
            self.resetSearch()
            if not self.Avoided():
                speed = self.getSpeedforDist(self.objdetect.found_objects[0][1])
                if self.inRange(self.objdetect.found_objects[0][1], 6, 10):
                    self.car.stop()
                    self.pickup_thread = True
                    Thread(target=self.checkIfPickupRange,args=()).start()
                else:
                    if self.objdetect.found_objects[0][1] < 6:
                        self.car.go_backwards(speed)
                    else:
                        if self.inRange(self.objdetect.found_objects[0][2], -40, 40):
                            self.car.go_foward(speed)
                        else:
                            if self.objdetect.found_objects[0][2] > 0:
                                self.car.turn_right(speed, both_wheels=False)
                            else:
                                self.car.turn_left(speed, both_wheels=False)
        elif not self.pickup_thread:
            self.setMode("Searching...")
                              
    def checkiffoundBin(self):
        if self.objdetect.found_bins and not self.drop_thread:
            self.setMode("Found Bin")
            self.resetSearch()
            if not self.Avoided():
                speed = self.getSpeedforDist(self.objdetect.found_bins[0][1])
                if self.objdetect.found_bins[0][1] < 20:
                    self.car.stop()
                    self.drop_thread = True
                    Thread(target=self.checkIfDropRange, args=()).start()
                else:
                    if self.inRange(self.objdetect.found_bins[0][2], -40, 40):
                        self.car.go_foward(speed)
                    else:
                        if self.objdetect.found_bins[0][2] > 0:
                            self.car.turn_right(speed, both_wheels=False)
                        else:
                            self.car.turn_left(speed, both_wheels=False)
        elif not self.drop_thread:
            self.setMode("Searching...")

    def doingSearchObject(self):
        while self.doSearch and not self.foundObject():
            self.Search()
        
        self.car.stop()
        self.search_thread = False
        
    def doingSearchBin(self):
        while self.doSearch and not self.foundBin():
            self.Search()
        
        self.car.stop()
        self.search_thread = False
        
    def Search(self):
        if not self.ultra.getValue(1) < self.F_ultra_range and not self.ultra.getValue(3) < self.B_ultra_range:
            if self.start_right:
                self.car.turn_right(65)
            else:
                self.car.turn_left(65)
            time.sleep(0.3)
            self.car.stop()
        elif self.ultra.getValue(1) < self.F_ultra_range:
            self.car.go_backwards(55)
            time.sleep(0.3)
            self.car.stop()
        elif self.ultra.getValue(3) < self.B_ultra_range:
            self.car.go_foward(55)
            time.sleep(0.3)
            self.car.stop()
        time.sleep(0.5)

    def Avoided(self):
        if not self.search_thread:
            if self.ultra.getValue(1) < self.F_ultra_range: #detected on front middle
                self.backwards_thread = True
                Thread(target=self.backwardsAvoid, args=()).start()
                return True
            if self.ultra.getValue(3) < self.B_ultra_range: #detected on back
                self.car.go_foward(40)
                return True
            if self.ultra.getValue(2) < self.FL_ultra_range: #detected on front left
                self.car.turn_right(50)
                self.start_right = True
                return True
            if self.ultra.getValue(0) < self.FR_ultra_range: #detected on front right
                self.car.turn_left(50)
                self.start_right = False
                return True
            return False
        else:
            return True
        
    def carControlBin(self):
        if not self.foundBin():
            if self.doSearch and not self.search_thread:
                self.search_thread = True
                Thread(target=self.doingSearchBin, args=()).start()
            elif not self.doSearch and not self.backwards_thread:
                if not self.Avoided():
                    self.car.go_foward(55)
                    
    def carControlObject(self):
        if not self.foundObject():
            if self.doSearch and not self.search_thread:
                self.search_thread = True
                Thread(target=self.doingSearchObject, args=()).start()
            elif not self.doSearch and not self.backwards_thread:
                if not self.Avoided():
                    self.car.go_foward(55)
                    
    def backwardsAvoid(self):
        self.car.stop()
        time.sleep(0.1)
        while self.ultra.getValue(1) < self.F_ultra_range and self.ultra.getValue(3) > self.B_ultra_range:
            self.car.go_backwards(50)
        self.car.stop()
        time.sleep(0.1)
        if self.ultra.getValue(0) < self.ultra.getValue(2):
            self.car.turn_left(60)
            self.start_right = False
        else:
            self.car.turn_right(60)
            self.start_right = True
        time.sleep(0.3)
        
        self.backwards_thread = False

    def toggleSearch(self):
        if self.doSearch:
            if self.searchCount > 25:
                self.searchCount = 0
                self.doSearch = False
        else:
            if self.searchCount > 70:
                self.searchCount = 0
                self.doSearch = True
        self.searchCount = self.searchCount + 1
                
    def resetSearch(self):
        self.doSearch = False
        self.searchCount = 0

    def setSearch(self):
        self.doSearch = True
        self.searchCount = 0
        
    def cleanup(self, error):
        self.doCleanup = True
        self.car.cleanup()
        self.objdetect.cleanup()
        self.ultra.cleanup()
        self.lcd.lcd_clear()
        self.lcd.lcd_display_string(error, 1)
    
robot = BarkBot(show_fps=False, show_gui=False, min_conf=0.75, disable_motors=False)
try:
    while True:
            if robot.show_fps:
                t1 = cv2.getTickCount()
            robot.ultra.receiveUltra()
            robot.checkUltras()
            robot.objdetect.doObjectDetect()
            if robot.armHasObject:
                robot.checkiffoundBin()
                robot.carControlBin()
            else:
                robot.checkifFoundObject()
                robot.carControlObject()
            robot.toggleSearch()
            if robot.show_fps:
                print('FPS: {0:.2f}'.format(robot.frame_rate_calc))
                t2 = cv2.getTickCount()
                time1 = (t2-t1)/robot.freq
                robot.frame_rate_calc = 1/time1
    
except: #KeyboardInterrupt: # If there is a KeyboardInterrupt (when you press ctrl+c), exit the program
    print("Exception")
    robot.cleanup("Exception")
