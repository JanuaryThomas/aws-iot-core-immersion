from uuid import uuid4
import time
import json
from datetime import datetime
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient, AWSIoTMQTTClient

sensor = None
try:
    from SensorRead import *

    sensor = MLX90614()
except ImportError:
    pass


def onMQTTMessage(message):
    print("Received: message: {}, topic: {}".format(message.payload, message.topic))


def onSubackCallback(mid, data):
    print("SUBACK id:{}, QoS: {}".format(mid, data))


AWS_ENDPOINT = "a3upko7gc2wjsg-ats.iot.eu-west-1.amazonaws.com"
ROOT_CA = "certificates/root-CA.crt"
CERTIFICATE = "certificates/8532aa4c20-certificate.pem.crt"
PRIVATE_KEY = "certificates/8532aa4c20-private.pem.key"
WEB_SOCKET = False
CLIENT_ID = "Themostat-{}".format(uuid4())
THING_NAME = "Themostat"
PORT = 443

awsIoTMQTTShadowClient = None
awsIoTMQTTShadowClient = AWSIoTMQTTShadowClient(CLIENT_ID)
awsIoTMQTTShadowClient.configureEndpoint(AWS_ENDPOINT, PORT)
awsIoTMQTTShadowClient.configureCredentials(ROOT_CA, PRIVATE_KEY, CERTIFICATE)
awsIoTMQTTShadowClient.configureAutoReconnectBackoffTime(1, 32, 20)
awsIoTMQTTShadowClient.configureConnectDisconnectTimeout(10)
awsIoTMQTTShadowClient.configureMQTTOperationTimeout(5)
awsIoTMQTTShadowClient.connect()

awsIoTMQTTClient = awsIoTMQTTShadowClient.getMQTTConnection()
# awsIoTMQTTClient = AWSIoTMQTTClient(CLIENT_ID)
# awsIoTMQTTClient.configureEndpoint(AWS_ENDPOINT, PORT)
# awsIoTMQTTClient.configureCredentials(ROOT_CA, PRIVATE_KEY, CERTIFICATE)

# AWSIoTMQTTClient connection configuration
awsIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
awsIoTMQTTClient.configureOfflinePublishQueueing(
    -1
)  # Infinite offline Publish queueing
awsIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
awsIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
awsIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec
awsIoTMQTTClient.onMessage = onMQTTMessage
# awsIoTMQTTClient.connect()


def thingCallBack(payload, status, token):
    print("Status: {}, Token: {}, Payload: {}".format(status, token, payload))


def onPubackCallback(mid):
    print("PUBACK id: {}".format(mid))


# waterPumpShadow = "/things/{}/shadow/name/waterPumpShadow".format(THING_NAME)
shadowHandler = awsIoTMQTTShadowClient.createShadowHandlerWithName("Fan", True)


count = 0
while True:
    try:
        data = {}
        data["temp"] = 0
        if sensor is not None:
            sensor = sensor.get_object_temperature()
            print("Sensor-{}".format(data))
            awsIoTMQTTClient.publishAsync(
                "espthemostat/temp", json.dumps(data), 1, ackCallback=onPubackCallback
            )
        time.sleep(2)
    except Exception as e:
        print("Error: {}".format(e))
