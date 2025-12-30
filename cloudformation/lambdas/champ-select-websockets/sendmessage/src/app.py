import json
import os
import boto3
from botocore.exceptions import ClientError
from typing import Any, Dict

ddb_client = boto3.client("dynamodb")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, int]:
    
    endpoint_url = "https://" + "/".join([
        event["requestContext"]["domainName"],
        event["requestContext"]["stage"]
    ])

    apigateway_client = boto3.client(
        "apigatewaymanagementapi",
        endpoint_url=endpoint_url
    )

    body = json.loads(event["body"])
    action = body["action"]

    match action:
        case "banChampion":
            ban_champion(
                apigateway_client,
                body["connectionId"],
                body["championId"]
            )
        case "selectChampion":
            select_champion(
                apigateway_client,
                body["connectionId"],
                body["championId"]
            )
        case _:
            return { "statusCode": 400, "body": "Invalid action" }

    return {"statusCode": 200}

def ban_champion(apigateway_client, connection_id: str, champion_id: str) -> None:
    message = json.dumps({
        "action": "banChampion",
        "championId": champion_id
    })
    send_message(apigateway_client, connection_id, message)

def select_champion(apigateway_client, connection_id: str, champion_id: str) -> None:
    message = json.dumps({
        "action": "selectChampion",
        "championId": champion_id
    })
    send_message(apigateway_client, connection_id, message)

def send_message(apigateway_client, connection_id: str, message: str) -> None:
    response = apigateway_client.post_to_connection(
        Data=message.encode("utf-8"),
        ConnectionId=connection_id
    )