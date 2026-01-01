import os
import boto3
import json
from typing import Any, Dict

ddb_client = boto3.client("dynamodb")


def lambda_handler(event, context):
    global APIGW_CLIENT

    endpoint_url = "https://" + "/".join(
        [event["requestContext"]["domainName"], event["requestContext"]["stage"]]
    )

    APIGW_CLIENT = boto3.client("apigatewaymanagementapi", endpoint_url=endpoint_url)

    try:
        qparams = event.get("queryStringParameters") or {}

        lobby_id = qparams.get("lobbyid")
        team_type = qparams.get("teamtype")
        connection_id = event["requestContext"]["connectionId"]

        if not lobby_id:
            return {"statusCode": 400, "body": "No Lobby Id passed"}

        lobby = get_lobby(table_name=os.environ["TABLE_NAME"], lobby_id=lobby_id)

        if not lobby:
            return {"statusCode": 400, "body": "No Lobby found"}

        blue_captain = lobby.get("blueCaptain", {}).get("S")
        red_captain = lobby.get("redCaptain", {}).get("S")
        spectators = json.loads(lobby.get("spectators", {}).get("S", "[]"))

        if team_type == "blue" and not blue_captain:
            lobby["blueCaptain"] = {"S": connection_id}
            send_message(
                connection_id, json.dumps({"action": "Role", "Role": "blueCaptain"})
            )
        elif team_type == "red" and not red_captain:
            lobby["redCaptain"] = {"S": connection_id}
            send_message(
                connection_id, json.dumps({"action": "Role", "Role": "redCaptain"})
            )
        else:
            spectators.append(connection_id)
            lobby["spectators"] = {"S": json.dumps(spectators)}
            send_message(
                connection_id, json.dumps({"action": "Role", "Role": "spectator"})
            )

        put_item(table_name=os.environ["TABLE_NAME"], item=lobby)

    except Exception as e:
        error_type = type(e).__name__
        error_message = str(e)
        print(f"Error occurred: {error_type}: {error_message}")
        return {"statusCode": 500, "body": f"{error_type}: {error_message}"}

    return {"statusCode": 200}


def send_message(connection_id: str, message: str) -> None:
    APIGW_CLIENT.post_to_connection(
        Data=message.encode("utf-8"), ConnectionId=connection_id
    )


def put_item(table_name: str, item: Dict[str, Any]) -> None:
    ddb_client.put_item(TableName=table_name, Item=item)


def get_lobby(table_name: str, lobby_id: str) -> Dict[str, Any]:
    response = ddb_client.get_item(
        TableName=table_name, Key={"lobbyId": {"S": f"LOBBY#{lobby_id}"}}
    )
    return response.get("Item", {})
