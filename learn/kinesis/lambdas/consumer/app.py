import json
import base64

    # result = base64.b64decode(record['Data'])
    # result = json.loads(result.decode('utf-8'))


def handler(event: dict, context: dict) -> dict:
    records = event['Records']
    data = []
    for record in records:
        result = base64.b64decode(record['kinesis']['data'])
        result = base64.b64decode(result)
        print('after', result.decode('utf-8'))
        data.append(
            json.loads(result.decode('utf-8'))
        )
    print(data)