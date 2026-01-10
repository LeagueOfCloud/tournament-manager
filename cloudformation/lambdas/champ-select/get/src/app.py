import json
import os
import boto3

ddb_client = boto3.client("dynamodb")


def lambda_handler(event, context):
    try:
        table_name = os.environ["TABLE_NAME"]

        scan_result = ddb_client.scan(TableName=table_name)

        lobbies = [deserialize_item(item) for item in scan_result.get("Items", [])]

        return response(200, {"lobbies": lobbies})

    except Exception as e:
        print(f"Error fetching lobbies: {e}")
        return response(500, {"error": "Internal server error"})


def deserialize_item(item):
    out = {}
    for key, value in item.items():
        dtype, dval = next(iter(value.items()))

        if dtype == "S":
            out[key] = dval
        elif dtype == "N":
            out[key] = int(dval)
        else:
            out[key] = dval  # fallback

    return out


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body, default=str),
    }
