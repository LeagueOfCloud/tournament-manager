import json
import os
import boto3
from botocore.exceptions import ClientError
from typing import Any, Dict

ddb_client = boto3.client("dynamodb")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, int]:
    
    print("event : " + json.dumps(event))
    
    endpoint_url = "https://" + "/".join([
        event["requestContext"]["domainName"],
        event["requestContext"]["stage"]
    ])

    print("endpoint_url : " + endpoint_url)

    connection_ids = scan_table(os.environ["TABLE_NAME"])

    print("connection_ids : " + str(connection_ids))

    apigateway_client = boto3.client(
        "apigatewaymanagementapi",
        endpoint_url=endpoint_url
    )

    for item in connection_ids.get("Items", []):
        print("item : " + str(item))
        body = json.loads(event["body"])
        message = body["message"]
        send_message(
            apigateway_client,
            item["connectionId"]["S"],
            message
        )

    return {"statusCode": 200}


def scan_table(table_name: str) -> Dict[str, Any]:
    response = ddb_client.scan(TableName=table_name)
    return response


def send_message(apigateway_client, connection_id: str, message: str) -> None:
    response = apigateway_client.post_to_connection(
        Data=message.encode("utf-8"),
        ConnectionId=connection_id
    )