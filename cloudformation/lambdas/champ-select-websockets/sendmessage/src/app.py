import json
import os
import boto3
import traceback
from typing import Any, Dict, Tuple

ddb_client = boto3.client("dynamodb")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, int]:
    global ALL_CONNECTIONS
    global APIGW_CLIENT

    endpoint_url = "https://" + "/".join(
        [event["requestContext"]["domainName"], event["requestContext"]["stage"]]
    )

    APIGW_CLIENT = boto3.client("apigatewaymanagementapi", endpoint_url=endpoint_url)
    ALL_CONNECTIONS = []

    connection_id = event["requestContext"]["connectionId"]
    body = json.loads(event["body"])

    lobby_id = body.get("LobbyId")

    lobby_item, lobby = get_lobby(lobby_id=lobby_id)

    if not lobby:
        send_message(connection_id, "No Lobby found")
    action = body["action"]

    ALL_CONNECTIONS = lobby["spectators"] + [lobby["blueCaptain"], lobby["redCaptain"]]
    match action:
        case "BanChampion":
            ban_champion(lobby, body["ChampionId"])
        case "SelectChampion":
            select_champion(lobby, body["ChampionId"])
        case "Start":
            if connection_id in [lobby["blueCaptain"], lobby["redCaptain"]]:
                broadcast_message(ALL_CONNECTIONS, json.dumps({"action": "Start"}))
        case "Sync":
            send_message(
                connection_id, json.dumps({"connectionId": connection_id, **lobby})
            )
        case _:
            send_message(connection_id, "Invalid Action")

    return {"statusCode": 200}


def ban_champion(lobby: object, champion_id: str) -> None:
    message = json.dumps({"action": "BanChampion", "ChampionId": champion_id})

    broadcast_message(APIGW_CLIENT, ALL_CONNECTIONS, message)


def select_champion(lobby: object, champion_id: str) -> None:
    message = json.dumps({"action": "SelectChampion", "ChampionId": champion_id})
    broadcast_message(APIGW_CLIENT, ALL_CONNECTIONS, message)


def send_message(connection_id: str, message: str) -> None:
    APIGW_CLIENT.post_to_connection(
        Data=message.encode("utf-8"), ConnectionId=connection_id
    )


def broadcast_message(connection_ids: list, message: str) -> None:
    connection_ids_filtered = list(filter(lambda c: c, connection_ids))
    for connection_id in connection_ids_filtered:
        send_message(APIGW_CLIENT, connection_id, message)


def put_item(item: Dict[str, Any]) -> None:
    ddb_client.put_item(TableName=os.environ["TABLE_NAME"], Item=item)


def get_lobby(lobby_id: str) -> Tuple[dict, Dict[str, Any]]:
    try:
        response = ddb_client.get_item(
            TableName=os.environ["TABLE_NAME"],
            Key={"lobbyId": {"S": f"LOBBY#{lobby_id}"}},
        )

        item = response["Item"]

        return (
            item,
            {
                "lobbyId": lobby_id,
                "blueCaptain": item.get("blueCaptain", {}).get("S"),
                "redCaptain": item.get("redCaptain", {}).get("S"),
                "spectators": json.loads(item["spectators"]["S"]),
                "state": item.get("state", {}).get("S"),
            },
        )

    except Exception as e:
        print(f"Error fetching lobby {lobby_id}: {e.response['Error']['Message']}")
        traceback.print_exc()
        return {}
