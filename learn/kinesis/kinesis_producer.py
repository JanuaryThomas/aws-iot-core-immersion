import boto3
import json
import base64
import time



client = boto3.client("kinesis")



# print(client.list_shards(
#     StreamName="KinesisIoTStream"
# ))

count = 0 
while count < 10:
    print("Sending {}".format(count))
    data = json.dumps({"temperature": 30, "time": int(time.time())})
    kinesis_payload = base64.b64encode(data.encode("utf-8"))
    client.put_record(
        StreamName="KinesisIoTStream",
        Data=kinesis_payload,
        PartitionKey="IoTCore"
    )
    count += 1