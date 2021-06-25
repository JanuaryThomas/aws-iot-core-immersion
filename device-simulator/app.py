from uuid import uuid4
import time
import json
from datetime import datetime
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient, AWSIoTMQTTClient

import smbus
from time import sleep
class MLX90614:

    MLX90614_RAWIR1 = 0x04
    MLX90614_RAWIR2 = 0x05
    MLX90614_TA = 0x06
    MLX90614_TOBJ1 = 0x07
    MLX90614_TOBJ2 = 0x08

    MLX90614_TOMAX = 0x20
    MLX90614_TOMIN = 0x21
    MLX90614_PWMCTRL = 0x22
    MLX90614_TARANGE = 0x23
    MLX90614_EMISS = 0x24
    MLX90614_CONFIG = 0x25
    MLX90614_ADDR = 0x0E
    MLX90614_ID1 = 0x3C
    MLX90614_ID2 = 0x3D
    MLX90614_ID3 = 0x3E
    MLX90614_ID4 = 0x3F

    _comm_retries = 5
    _comm_sleep_amount = 0.1

    def __init__(self, address: hex = 0x5A, bus_num: int = 1) -> None:

        self._address = address
        self._bus_num = bus_num
        self.bus = smbus.SMBus(bus=bus_num)

    @property
    def address(self) -> hex:
        return self._address

    @address.setter
    def address(self, address: hex):
        self._address = address

    @property
    def bus_num(self) -> int:
        return self._bus_num

    @bus_num.setter
    def bus_num(self, bus_num: int):
        self._bus_num = bus_num

    def read_register(self, register_address: hex):
        error = None
        for i in range(self._comm_retries):
            try:
                return self.bus.read_word_data(self._address, register_address)
            except IOError as _error:
                error = _error
                sleep(self._comm_sleep_amount)
        raise error

    def data_to_temp(self, data: hex) -> float:
        temperature: float = (data * 0.02) - 273.15
        return temperature

    def get_ambient_temperature(self) -> float:
        data: hex = self.read_register(self.MLX90614_TA)
        return self.data_to_temp(data)

    def get_object_temperature(self) -> float:
        data: hex = self.read_register(self.MLX90614_TOBJ1)
        return self.data_to_temp(data)


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
        data["data"] = 0
        data["timestamp"] = int(time.time())
        sensor = MLX90614()
        if sensor is not None:
            sensor = sensor.get_object_temperature()
            data["data"] = sensor
            print("Sensor-{}".format(data))
            awsIoTMQTTClient.publishAsync(
                "espthemostat/temp", json.dumps(data), 1, ackCallback=onPubackCallback
            )
        time.sleep(2)
    except Exception as e:
        print("Error: {}".format(e))
