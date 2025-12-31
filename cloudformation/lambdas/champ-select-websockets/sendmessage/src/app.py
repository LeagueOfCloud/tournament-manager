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

    connection_id = event["requestContext"]["connectionId"]
    body = json.loads(event["body"])

    lobby_id = body.get("LobbyId")

    lobby = get_lobby(
        lobby_id=lobby_id
    )

    if not lobby:
        send_message(apigateway_client, connection_id, "No Lobby found")

    action = body["action"]
    
    match action:
        case "BanChampion":
            ban_champion(
                apigateway_client,
                connection_id,
                body["ChampionId"]
            )
        case "SelectChampion":
            select_champion(
                apigateway_client,
                connection_id,
                body["ChampionId"]
            )
        case _:
            send_message(apigateway_client, connection_id, "Invalid Action")

    return {"statusCode": 200}

def ban_champion(apigateway_client, lobby: object, champion_id: str) -> None:
    message = json.dumps({
        "action": "banChampion",
        "championId": champion_id
    })
    broadcast_message(apigateway_client, lobby["spectators"] + [lobby["blueCaptain"], lobby["redCaptain"]], message)

def select_champion(apigateway_client, lobby: object, champion_id: str) -> None:
    message = json.dumps({
        "action": "selectChampion",
        "championId": champion_id
    })
    broadcast_message(apigateway_client, lobby["spectators"] + [lobby["blueCaptain"], lobby["redCaptain"]], message)

def send_message(apigateway_client, connection_id: str, message: str) -> None:
    apigateway_client.post_to_connection(
        Data=message.encode("utf-8"),
        ConnectionId=connection_id
    )

def broadcast_message(apigateway_client, connection_ids: list[str], message: str) -> None:
    for connection_id in connection_ids:
        send_message(apigateway_client, connection_id, message)

def get_lobby(lobby_id: str) -> Dict[str, Any]:
    try:
        response = ddb_client.get_item(
            TableName=os.environ["TABLE_NAME"],
            Key={"lobbyId": {"S": f"LOBBY#{lobby_id}"}}
        )

        item = response["Item"]

        return {
            "lobbyId": lobby_id,
            "blueCaptain": item["blueCaptain"]["S"],
            "redCaptain": item["redCaptain"]["S"],
            "spectators": json.loads(item["spectators"]["S"]),
        }
    
    except ClientError as e:
        print(f"Error fetching lobby {lobby_id}: {e.response['Error']['Message']}")
        return {}