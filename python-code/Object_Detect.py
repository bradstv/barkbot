import os
import argparse
import cv2
import numpy as np
import sys
import time
from threading import Thread
from pyzbar import pyzbar
import importlib.util

class VideoStream:
    def __init__(self,resolution=(416,416)):
        self.stream = cv2.VideoCapture(0)
        ret = self.stream.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        ret = self.stream.set(3,resolution[0])
        ret = self.stream.set(4,resolution[1])
          
        self.grabbed, frame = self.stream.read()
        self.frame = cv2.rotate(frame, cv2.ROTATE_180) 
        
        self.stopped = False

    def start(self):
        Thread(target=self.update,args=()).start()
        return self

    def update(self):
        while True:
            if self.stopped:
                self.stream.release()
                return
                
            self.grabbed, frame = self.stream.read()
            self.frame = cv2.rotate(frame, cv2.ROTATE_180) 

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True
        
MODEL_NAME = 'custom_model_lite_updated'
GRAPH_NAME = 'detect.tflite'
LABELMAP_NAME = 'labelmap.txt'
knownHeights = {
  "blue-ball": 1.9,
  "green-ball": 1.9,
  "orange-ball": 1.9,
  "yellow-ball": 2,
  "red-ball": 1.9,
  "drop-bin": 3.375
}

pkg = importlib.util.find_spec('tflite_runtime')
if pkg:
    from tflite_runtime.interpreter import Interpreter
else:
    from tensorflow.lite.python.interpreter import Interpreter
  
CWD_PATH = os.getcwd()
PATH_TO_CKPT = os.path.join(CWD_PATH,MODEL_NAME,GRAPH_NAME)
PATH_TO_LABELS = os.path.join(CWD_PATH,MODEL_NAME,LABELMAP_NAME)

with open(PATH_TO_LABELS, 'r') as f:
    labels = [line.strip() for line in f.readlines()]
    
class ObjectDetect:
    def __init__(self, resolution=(416,416), min_conf_threshold=0.7, show_gui=True, threads=3):
        self.found_objects = []
        self.found_bins = []
        self.min_conf_threshold = min_conf_threshold
        self.imW = resolution[0]
        self.imH = resolution[1]
        self.show_gui = show_gui
        self.interpreter = Interpreter(model_path=PATH_TO_CKPT, num_threads=threads)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        self.height = self.input_details[0]['shape'][1]
        self.width = self.input_details[0]['shape'][2]
        self.floating_model = (self.input_details[0]['dtype'] == np.float32)
        outname = self.output_details[0]['name']
        if ('StatefulPartitionedCall' in outname):
            self.boxes_idx, self.classes_idx, self.scores_idx = 1, 3, 0
        else:
            self.boxes_idx, self.classes_idx, self.scores_idx = 0, 1, 2
        self.videostream = VideoStream(resolution=(resolution[0],resolution[1])).start()
        
    def getDistanceFromCamera(self, obj, max, min): #in inches
        height = max - min
        return (knownHeights[obj]*462)/height
        
    def getCenterofObj(self, xmax, xmin): #in pixels
        return int((xmin + xmax) / 2)
        
    def doObjectDetect(self):
        frame1 = self.videostream.read()
        frame = frame1.copy()
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_resized = cv2.resize(frame_rgb, (self.width, self.height))
        input_data = np.expand_dims(frame_resized, axis=0)
                
        if self.floating_model:
            input_data = (np.float32(input_data) - 127.5) / 127.5

        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        self.interpreter.invoke()

        boxes = self.interpreter.get_tensor(self.output_details[self.boxes_idx]['index'])[0]
        classes = self.interpreter.get_tensor(self.output_details[self.classes_idx]['index'])[0]
        scores = self.interpreter.get_tensor(self.output_details[self.scores_idx]['index'])[0]
        
        found_objects = []
        found_bins = []
        for i in range(len(scores)):
            if ((scores[i] > self.min_conf_threshold) and (scores[i] <= 1.0)):

                ymin = int(max(1,(boxes[i][0] * self.imH)))
                xmin = int(max(1,(boxes[i][1] * self.imW)))
                ymax = int(min(self.imH,(boxes[i][2] * self.imH)))
                xmax = int(min(self.imW,(boxes[i][3] * self.imW)))
                object_name = labels[int(classes[i])]
                distance = self.getDistanceFromCamera(object_name, xmax, xmin)
                x_error = self.getCenterofObj(xmax, xmin) - self.imW/2
                
                if self.show_gui:
                    cv2.rectangle(frame, (xmin,ymin), (xmax,ymax), (10, 255, 0), 2)
                    label = f"{object_name}: {int(scores[i]*100)}% ({int(distance)}in)"
                    labelSize, baseLine = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
                    label_ymin = max(ymin, labelSize[1] + 10)
                    cv2.rectangle(frame, (xmin, label_ymin-labelSize[1]-10), (xmin+labelSize[0], label_ymin+baseLine-10), (255, 255, 255), cv2.FILLED)
                    cv2.putText(frame, label, (xmin, label_ymin-7), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
                    
                if object_name == "drop-bin":
                    found_bin = [object_name, distance, x_error]
                    found_bins.append(found_bin)
                else:
                    found_object = [object_name, distance, x_error]
                    found_objects.append(found_object)
                
        found_objects.sort(key=lambda obj:obj[1]) #sort found objects by distance, closest is always first in array
        found_bins.sort(key=lambda obj:obj[1])
        self.found_objects = found_objects
        self.found_bins = found_bins
                    
        if self.show_gui:
            cv2.imshow('Object detector', frame)
            cv2.waitKey(1)
        
    def cleanup(self):
        self.videostream.stop()
        cv2.destroyAllWindows()
