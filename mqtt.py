# python3 mqtt.py --ca_file ~/certs/AmazonRootCA1.pem --cert ~/certs/1d6cd-certificate.pem.crt --key ~/certs/1d6cd-private.pem.key --endpoint a1io7cze9x1oli-ats.iot.us-east-1.amazonaws.com



# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0.

from awscrt import mqtt, http
from awsiot import mqtt_connection_builder
import sys
import threading
import time
import json
from utils.command_line_utils import CommandLineUtils
import time
import calendar
from datetime import datetime  
import board
import adafruit_dht
import boto3

current_GMT = time.gmtime()

#time_stamp = calendar.timegm(current_GMT)

from picamera import PiCamera
import RPi.GPIO as GPIO
GPIO.setwarnings(False)
from hx711 import HX711
dhtDevice = adafruit_dht.DHT11(board.D27)


camera = PiCamera()
camera.resolution = (1024, 768)
IMG_NAME = ""
s3 = boto3.resource('s3')
BUCKET_NAME = 'team01-image'
BUCKET_REGION = 'us-east-1'

##### HX711 Setup ##############
referenceUnit = 465

def cleanAndExit():
    print("Cleaning...")

    GPIO.cleanup()
        
    print("Bye!")
    sys.exit()

hx = HX711(5, 6)
hx.set_reading_format("MSB", "MSB")
hx.set_reference_unit(referenceUnit)
hx.reset()
hx.tare()

print("Tare done! Add weight now...")



cmdData = CommandLineUtils.parse_sample_input_pubsub()

received_count = 0
received_all_event = threading.Event()

MQTT_Topic = "team01/final"
MQTT_Msg = ""
publish_count = 1
weightVal = 0.0
temperature_c = 0.0
humidity = 0

# Callback when connection is accidentally lost.
def on_connection_interrupted(connection, error, **kwargs):
    print("Connection interrupted. error: {}".format(error))


# Callback when an interrupted connection is re-established.
def on_connection_resumed(connection, return_code, session_present, **kwargs):
    print("Connection resumed. return_code: {} session_present: {}".format(return_code, session_present))

    if return_code == mqtt.ConnectReturnCode.ACCEPTED and not session_present:
        print("Session did not persist. Resubscribing to existing topics...")
        resubscribe_future, _ = connection.resubscribe_existing_topics()

        # Cannot synchronously wait for resubscribe result because we're on the connection's event-loop thread,
        # evaluate result with a callback instead.
        resubscribe_future.add_done_callback(on_resubscribe_complete)


def on_resubscribe_complete(resubscribe_future):
    resubscribe_results = resubscribe_future.result()
    print("Resubscribe results: {}".format(resubscribe_results))

    for topic, qos in resubscribe_results['topics']:
        if qos is None:
            sys.exit("Server rejected resubscribe to topic: {}".format(topic))


# Callback when the subscribed topic receives a message
def on_message_received(topic, payload, dup, qos, retain, **kwargs):
    print("Received message from topic '{}': {}".format(topic, payload))
    global received_count
    received_count += 1
    # receive data
    payload = json.loads(payload.decode('utf-8'))
    take_a_picture(payload)
    
    if received_count == cmdData.input_count:
        received_all_event.set()

def take_a_picture(payload):
    #if payload['pi_camera'] == True:   
   
    return            


if __name__ == '__main__':
    # Create the proxy options if the data is present in cmdData
    proxy_options = None
    if cmdData.input_proxy_host is not None and cmdData.input_proxy_port != 0:
        proxy_options = http.HttpProxyOptions(
            host_name=cmdData.input_proxy_host,
            port=cmdData.input_proxy_port)

    # Create a MQTT connection from the command line data
    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint=cmdData.input_endpoint,
        port=cmdData.input_port,
        cert_filepath=cmdData.input_cert,
        pri_key_filepath=cmdData.input_key,
        ca_filepath=cmdData.input_ca,
        on_connection_interrupted=on_connection_interrupted,
        on_connection_resumed=on_connection_resumed,
        client_id=cmdData.input_clientId,
        clean_session=False,
        keep_alive_secs=30,
        http_proxy_options=proxy_options)

    if not cmdData.input_is_ci:
        print(f"Connecting to {cmdData.input_endpoint} with client ID '{cmdData.input_clientId}'...")
    else:
        print("Connecting to endpoint with client ID")
    connect_future = mqtt_connection.connect()

    # Future.result() waits until a result is available
    connect_future.result()
    print("Connected!")

    message_count = cmdData.input_count
    message_topic = MQTT_Topic
    message_string = MQTT_Msg

    # Subscribe
    print("Subscribing to topic '{}'...".format(message_topic))
    subscribe_future, packet_id = mqtt_connection.subscribe(
        topic=message_topic,
        qos=mqtt.QoS.AT_LEAST_ONCE,
        callback=on_message_received)

    subscribe_result = subscribe_future.result()
    print("Subscribed with {}".format(str(subscribe_result['qos'])))

    

    ##### Get weight ##################
    try:
        weightVal = hx.get_weight(5)
        print("HX711: {:.1f}".format(abs(weightVal)))
        hx.power_down()
        hx.power_up()
        time.sleep(0.1)   

    except(KeyboardInterrupt, SystemExit):
        cleanAndExit()

    ##### Get DHT11 Sensor ############
    try:
        # Print the values to the serial port
        temperature_c = dhtDevice.temperature
        temperature_f = temperature_c * (9 / 5) + 32
        humidity = dhtDevice.humidity
        print(
            "Temp: {:.1f} C    Humidity: {}% ".format(
                temperature_c, humidity
            )
        )

    except Exception as error:
        dhtDevice.exit()
        raise error
    
    ###### take a picture #############
    try:
        print("...init camera...")
        ## pi camera ##
        camera.start_preview()
        time.sleep(0.1)
        camera.capture('/home/pi/picamera.jpg')
        camera.stop_preview()
        #print("...")
        # camera.close()

    except:
        print("error")


    time.sleep(1.0) 
     
        

    ##### MQTT push message ##################
    print("Publishing message to topic")
    # message = '"{hx711":{hx711},' \
    #           '"temperature":25.0,' \
    #           '"ultra_sonic":100,' \
    #           '"sound_snd":50,' \
    #           '"update_time":"2023-06-04 02:09:00",' \
    #           '"publish_count":{count}}'.format(hx711=weightVal, count=publish_count) \
              
    

    # message_json = json.dumps(message)
    # mqtt_connection.publish(
    #     topic=message_topic,
    #     payload=message_json,
    #     qos=mqtt.QoS.AT_LEAST_ONCE)
    # time.sleep(1)

    
    if message_count == 0:
        print("Sending messages until program killed")
    else:
        print("Sending message(s)")

    
    # while (publish_count <= message_count) or (message_count == 0):
    while(weightVal):
        
        ##### Get time.now ###################
        current_time = datetime.now()
        time_stamp = current_time.timestamp()
        date_time = datetime.fromtimestamp(time_stamp)
        str_date = date_time.strftime("%Y-%m-%d")
        str_time = date_time.strftime("%H:%M")
        print("timestamp:", time_stamp)
        print("The date and time is:", str_time)


        ###### take a picture #############
        try:
            print("...init camera...")
            ## pi camera ##
            camera.start_preview()
            time.sleep(0.1)
            camera.capture('/home/pi/cloudprog_finalProject/picamera.jpg')
            camera.stop_preview()
            #print("...")
            # camera.close()

            IMG_NAME = 'picamera.jpg'
            data = open(IMG_NAME, 'rb')
            s3.Bucket(BUCKET_NAME).put_object(Key=IMG_NAME, Body=data)
            print("take a picture...")

        except:
            print("error")

        ##### Get weight ##################
        try:
            weightVal = hx.get_weight(5)
            #message = '{"hx711":'+str(weightVal)+'}'
            message_string = '{"weight":'+str(abs(round(weightVal)))+', "temperature":'+ str(temperature_c) +', "humidity":' + str(humidity)+', "counter":' + str(publish_count) +', "timestamp":'+ str(round(time_stamp)) +', "formatdate":'+ str(str_date) +', "formattime":'+ str(str_time)+'}'
            message = "{}".format(message_string)
            #print(weightVal)
            hx.power_down()
            hx.power_up()
            time.sleep(0.1)   

        except(KeyboardInterrupt, SystemExit):
            cleanAndExit()

        print("Publishing message to topic '{}': {}".format(message_topic, message))
        message_json = json.dumps(message)
        mqtt_connection.publish(
            topic=message_topic,
            payload=message_json,
            qos=mqtt.QoS.AT_LEAST_ONCE)
        time.sleep(5)
        publish_count += 1

    # Wait for all messages to be received.
    # This waits forever if count was set to 0.
    if message_count != 0 and not received_all_event.is_set():
        print("Waiting for all messages to be received...")

    received_all_event.wait()
    print("{} message(s) received.".format(received_count))

    # Disconnect
    print("Disconnecting...")
    disconnect_future = mqtt_connection.disconnect()
    disconnect_future.result()
    print("Disconnected!")

