import boto3
import json
import base64
import time



client = boto3.client("kinesis")

stream_details = client.describe_stream(
    StreamName="KinesisIoTStream"
)

shard_id = stream_details['StreamDescription']['Shards'][0]['ShardId']

print(shard_id)

shard_iteratior = client.get_shard_iterator(
    StreamName="KinesisIoTStream",
    ShardId=shard_id, 
    ShardIteratorType='TRIM_HORIZON'
)

shard_iteratior = shard_iteratior['ShardIterator']
records = client.get_records(
    ShardIterator=shard_iteratior, Limit=10000
)

for record in records['Records']:
    result = base64.b64decode(record['Data'])
    result = json.loads(result.decode('utf-8'))

    print(result['time'])