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

from awscrt import io, http, auth, mqtt
from awsiot import mqtt_connection_builder
from uuid import uuid4

import os
import sys
import time

# ---- MQTT Server information -------------

user_path = os.path.expanduser('~')
endpoint  = "a1lc00egar11av-ats.iot.us-west-1.amazonaws.com"
ca_file   = user_path+"/certs/Amazon-root-CA-1.pem"
cert      = user_path+"/certs/certificate.pem.crt"
priv_key  = user_path+"/certs/private.pem.key"

topic     = "polyver1_data"
client_id = "polyver1-" + str(uuid4())

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

def on_message_received(topic, payload, dup, qos, retain, **kwargs):
    print("Received message from topic '{}': {}".format(topic, payload))
    # global received_count
    # received_count += 1
    # if received_count == cmdUtils.get_command("count"):
    #     received_all_event.set()

# ---- Main program ------------------------

if __name__ == "__main__":
    # Build connection
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

    # Subcribe to topic
    print("Subscribing to topic '{}'...".format(topic))
    subscribe_future, packet_id = mqtt_connection.subscribe(
        topic=topic,
        qos=mqtt.QoS.AT_LEAST_ONCE,
        callback=on_message_received)
    subscribe_result = subscribe_future.result()
    print("Subscribed with {}".format(str(subscribe_result["qos"])))
   
    # Test send message
    message = "test message from polyver1"
    print("Publishing message to topic '{}': {}".format(topic, message))
    #message_json = json.dumps(message)
    mqtt_connection.publish(
        topic=topic,
        payload=message,
        qos=mqtt.QoS.AT_LEAST_ONCE)
    
    # Wait message to send and be received
    time.sleep(5)

    # Finshed, disconnect from MQTT server
    print("Disconnecting...")
    disconnect_future = mqtt_connection.disconnect()
    disconnect_future.result()
    print("Disconnected!")

