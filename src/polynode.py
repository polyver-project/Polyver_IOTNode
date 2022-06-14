#################################################
# File:    polynode.py
# Author:  Diego Andrade (bets636@gmail.com)
# Date:    May 10, 2022
# Purpose: End point / communcator for Polyvers 
#          to MQTT serve and ultimately frontend
# 
# Notes: Using signing region
# 
#################################################

from asyncio import tasks
from awscrt import io, http, auth, mqtt
from awsiot import mqtt_connection_builder

import serial

import os
import sys
import time
import threading
import json

from polyverController import PolyverController

# ---- Constants ---------------------------
SER_UPDATE_RATE_MS = 100
IMPORTANT_COMMANDS = ['m:0', 'm: 0', 'm:1', 'm: 1','l:0', 'l: 0', 'r:0', 'r: 0']

# ---- MQTT Server information -------------
user_path = os.path.expanduser('~')
endpoint  = "a1lc00egar11av-ats.iot.us-west-1.amazonaws.com"
ca_file   = user_path+"/certs/Amazon-root-CA-1.pem"
cert      = user_path+"/certs/certificate.pem.crt"
priv_key  = user_path+"/certs/private.pem.key"

client_id = "polyver1"

# ---- Globals -----------------------------
mqtt_connection = None
ser = None
ser_last_update = 0

# ---- Callback MQTT functions -------------
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

        for topic, qos in resubscribe_results["topics"]:
            if qos is None:
                sys.exit("Server rejected resubscribe to topic: {}".format(topic))

# ---- MQTT Functions ----------------------
def mqtt_connect():
    # Build connection
    global mqtt_connection
    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint=endpoint,
        cert_filepath=cert,
        pri_key_filepath=priv_key,
        ca_filepath=ca_file,
        on_connection_interrupted=on_connection_interrupted,
        on_connection_resumed=on_connection_resumed,
        client_id=client_id,
        clean_session=False,
        keep_alive_secs=30)

    # Connect to MQTT server
    print("Connecting to {} with cliend id '{}'".format(endpoint, client_id))
    connect_future = mqtt_connection.connect()
    connect_future.result()     # wait for result to be ready
    print("Connected!")

def mqtt_disconnect():
    if mqtt_connection is None:
        print("No connection found")
        return
    
    print("Disconnecting...")
    disconnect_future = mqtt_connection.disconnect()
    disconnect_future.result()
    print("Disconnected!")

def mqtt_subscribe(topic, callback):
    print("Subscribing to topic '{}'...".format(topic))
    subscribe_future, packet_id = mqtt_connection.subscribe(
        topic=topic,
        qos=mqtt.QoS.AT_LEAST_ONCE,
        callback=callback)
    subscribe_result = subscribe_future.result()
    print("Subscribed with {}".format(str(subscribe_result["qos"])))

def mqtt_send(message, topic):
    print("Publishing message to topic '{}': {}".format(topic, message))
    mqtt_connection.publish(
        topic=topic,
        payload=message,
        qos=mqtt.QoS.AT_LEAST_ONCE)

# --- Thread Task --------------------------
def arduino_rx():
    while (True):
        cmdLine = str(ser.readline()).encode('utf8', 'ignore')
        print(cmdLine)

        if b'lat' in cmdLine:
            gps_data = cmdLine.split(b',')
            gps_lat  = gps_data[1].decode("utf-8")
            gps_lon  = gps_data[3].decode("utf-8").replace('\\r', '').replace('\\n', '').replace('\'', '')

            gps_data_formatted = '{"lat": ' + gps_lat + ',"long": ' + gps_lon + ', "rover": "Dr. Polyver"}'
            mqtt_send(gps_data_formatted, 'telemetry')

def controller_rx():
    controller = PolyverController(event_callback=send_command,interface="/dev/input/js0", connecting_using_ds4drv=False)
    controller.listen(timeout=3600)

# ---- Main program ------------------------
def on_command_received(topic, payload, dup, qos, retain, **kwargs):
    # Pre-process command
    payload_json = json.loads(payload)

    # Parse command
    output_str = ''
    if (payload_json['cmd'] == 'left'):
        output_str = 'x:-6 y:0'
    elif (payload_json['cmd'] == 'right'):
        output_str = 'x:6 y:0'
    elif (payload_json['cmd'] == 'up'):
        output_str = 'x:0 y:6'
    elif (payload_json['cmd'] == 'down'):
        output_str = 'x:0 y:-6'

    # Send to Arduino
    send_command(output_str)

def send_command(command):
    current_ms = int(round(time.time() * 1000))

    global ser_last_update

    # Slow down output rate unless important command
    if (((current_ms - ser_last_update)  < SER_UPDATE_RATE_MS) and not (command in IMPORTANT_COMMANDS)):
        return
    ser_last_update = current_ms

    if (command.find('\n') == -1): 
        command += '\n'
    ser.write(command.encode('utf8', 'ignore'))


if __name__ == "__main__":
    # Open serial connection 
    ser = serial.Serial('/dev/ttyUSB1')

    # Create thread for listening to arduino communication and wait for arduino to restart program
    t_arduino_rx = threading.Thread(target=arduino_rx)
    t_arduino_rx.start()
    time.sleep(0.5)

    # Create thread for handling controller input 
    t_controller_rx = threading.Thread(target=controller_rx)
    t_controller_rx.start()
    
    # Connect to MQTT server
    mqtt_connect()

    # Subcribe to topic
    mqtt_subscribe("Dr. Polyver/command", on_command_received)
   

   
    # Test send message
    # mqtt_send("test message from polyver1", "polyver1/telemetry")

    # Setting control mode to path follow by default
    send_command('m: 1')

    # Wait for threads to finish (or get killed)
    try:
        t_controller_rx.join()
    except:
        pass

    try:
        t_arduino_rx.join()
    except:
        pass

    # Clean up
    mqtt_disconnect()

    try:
        ser.close()
    except:
        pass

    print("Fin")
