from enum import Enum
import json
import os
import boto3
import traceback
from typing import Any, Dict, Tuple

ddb_client = boto3.client("dynamodb")


class State(Enum):
    Waiting = 1
    BlueTeamBan = 2
    RedTeamBan = 3
    BlueTeamPick = 4
    RedTeamPick = 5


STATE_RULES = {
    State.BlueTeamBan.name: {
        "action": "BanChampion",
        "captain": "blueCaptain",
    },
    State.RedTeamBan.name: {
        "action": "BanChampion",
        "captain": "redCaptain",
    },
    State.BlueTeamPick.name: {
        "action": "SelectChampion",
        "captain": "blueCaptain",
    },
    State.RedTeamPick.name: {
        "action": "SelectChampion",
        "captain": "redCaptain",
    },
}


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
        return {"statusCode": 404}

    action = body["action"]

    ALL_CONNECTIONS = lobby["spectators"] + [
        lobby["blueCaptain"],
        lobby["redCaptain"],
    ]

    match action:
        case "BanChampion":
            ban_champion(lobby, body["ChampionId"], connection_id)

        case "SelectChampion":
            select_champion(lobby, body["ChampionId"], connection_id)

        case "Start":
            if connection_id in [lobby["blueCaptain"], lobby["redCaptain"]]:
                broadcast_message(ALL_CONNECTIONS, json.dumps({"action": "Start"}))
            else:
                send_message(connection_id, "Only captains can start the match")

        case "Sync":
            send_message(
                connection_id,
                json.dumps({"connectionId": connection_id, **lobby}),
            )

        case _:
            send_message(connection_id, "Invalid Action")

    update_lobby(lobby)
    return {"statusCode": 200}


def authorize_action(
    lobby: Dict[str, Any],
    connection_id: str,
    action: str,
) -> bool:
    state = lobby.get("state")

    rule = STATE_RULES.get(state)
    if not rule:
        send_message(connection_id, "Invalid lobby state")
        return False

    if rule["action"] != action:
        send_message(
            connection_id,
            f"Action '{action}' not allowed in state '{state}'",
        )
        return False

    expected_captain = lobby.get(rule["captain"])
    if connection_id != expected_captain:
        send_message(connection_id, "Slow down cowboy its not your turn")
        return False

    return True


def ban_champion(
    lobby: Dict[str, Any],
    champion_id: str,
    connection_id: str,
) -> None:
    if not authorize_action(lobby, connection_id, "BanChampion"):
        return
    if lobby["state"] == "BlueTeamBan":
        lobby["state"] = State.RedTeamBan.name
    elif lobby["state"] == "RedTeamBan":
        lobby["state"] = State.BlueTeamBan.name
    lobby["bans"].append(champion_id)
    message = json.dumps({"action": "BanChampion", "ChampionId": champion_id})
    broadcast_message(ALL_CONNECTIONS, message)


def select_champion(
    lobby: Dict[str, Any],
    champion_id: str,
    connection_id: str,
) -> None:
    if not authorize_action(lobby, connection_id, "SelectChampion"):
        return
    if lobby["state"] == "BlueTeamPick":
        lobby["state"] = State.RedTeamPick.name
        lobby["blueTeamChampions"].append(champion_id)
    elif lobby["state"] == "RedTeamPick":
        lobby["state"] = State.BlueTeamPick.name
        lobby["redTeamChampions"].append(champion_id)
    message = json.dumps({"action": "SelectChampion", "ChampionId": champion_id})
    broadcast_message(ALL_CONNECTIONS, message)


def send_message(connection_id: str, message: str) -> None:
    APIGW_CLIENT.post_to_connection(
        Data=message.encode("utf-8"),
        ConnectionId=connection_id,
    )


def broadcast_message(connection_ids: list, message: str) -> None:
    for connection_id in filter(None, connection_ids):
        send_message(connection_id, message)


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
                "bans": json.loads(item["bans"]["S"]),
                "redTeamChampions": json.loads(item["redTeamChampions"]["S"]),
                "blueTeamChampions": json.loads(item["blueTeamChampions"]["S"]),
            },
        )

    except Exception as e:
        print(f"Error fetching lobby {lobby_id}: {e}")
        traceback.print_exc()
        return {}, {}


def update_lobby(lobby: Dict[str, Any]) -> None:
    ddb_client.put_item(
        TableName=os.environ["TABLE_NAME"],
        Item={
            "lobbyId": {"S": f"LOBBY#{lobby['lobbyId']}"},
            "blueCaptain": {"S": lobby["blueCaptain"]},
            "redCaptain": {"S": lobby["redCaptain"]},
            "spectators": {"S": json.dumps(lobby["spectators"])},
            "state": {"S": lobby["state"]},
            "bans": {"S": json.dumps(lobby["bans"])},
            "redTeamChampions": {"S": json.dumps(lobby["redTeamChampions"])},
            "blueTeamChampions": {"S": json.dumps(lobby["blueTeamChampions"])},
        },
    )