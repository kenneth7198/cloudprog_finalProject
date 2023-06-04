from gpiozero import DistanceSensor
from time import sleep

ultrasonic = DistanceSensor(17, 4)


    
while True:
    print('Distance to nearest object is', ultrasonic.distance*1000, 'cm')
    sleep(0.2)
    
    #ultrasonic.wait_for_in_range()
    #print("In range")
    
    
    #ultrasonic.wait_for_out_of_range()
    #print("Out of range")
  
    

