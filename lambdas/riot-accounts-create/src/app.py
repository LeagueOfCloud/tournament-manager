import json
import os
import pymysql
import requests
from datetime import datetime

INSERT_PLAYER_SQL = """
    INSERT INTO riot_accounts (account_name, account_puuid, player_id, is_primary)
    VALUES (%s, %s, %s, %s)
"""


def get_player_puuid(summoner_name: str, region: str = "europe") -> str:
    api_key = os.environ["RIOT_API_KEY"]

    if "#" not in summoner_name:
        raise ValueError("Summoner name must include tag (e.g., 'Player#EUW1').")

    name, tag = summoner_name.split("#", 1)
    url = f"https://{region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}"

    headers = {"X-Riot-Token": api_key}

    print(f"Requesting PUUID for {summoner_name} from Riot API...")

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        puuid = response.json().get("puuid")
        print(f"PUUID successfully retrieved for {summoner_name}.")
        return puuid

    elif response.status_code == 404:
        print(f"Player '{summoner_name}' not found (404). Check the name and tag.")
    elif response.status_code == 403:
        print("Forbidden (403): Invalid or expired API key.")
    elif response.status_code == 429:
        print("Rate limit exceeded (429): Too many requests.")
    elif response.status_code == 500:
        print("Internal server error (500) on Riot API.")
    else:
        print(f"Unexpected error: {response.status_code} - {response.text}")

    raise Exception(
        f"Failed to fetch PUUID for {summoner_name}: {response.status_code}"
    )


def validate_account_data(account_data) -> bool:
    if not all(account_data.get(field, "").strip() for field in ["account_name"]):
        return False

    try:
        int(account_data.get("player_id", ""))
        
        if not isinstance(account_data.get("is_primary"), bool):
            raise TypeError
    except (ValueError, TypeError):
        return False

    return True


def create_connection() -> pymysql.Connection:
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        cursorclass=pymysql.cursors.DictCursor,
    )


def lambda_handler(event, context):
    request_id = context.aws_request_id
    account_data = json.loads(event["body"])

    print(f"{request_id} Reveived account_data: {str(account_data)}")

    if not validate_account_data(account_data):
        print(f"{request_id} Invalid account_data for request_id")
        return {
            "statusCode": 400,
        }

    account_name = account_data.get("account_name")
    player_id = account_data.get("player_id")
    is_primary = account_data.get("is_primary")

    try:
        account_puuid = get_player_puuid(account_name)
    except Exception as e:
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(f"{e}"),
        }

    connection = None

    try:

        print(f"{request_id} Connecting to db")

        connection = create_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                INSERT_PLAYER_SQL, (account_name, account_puuid, player_id, "true" if is_primary else "false")
            )
            connection.commit()
            insert_id = cursor.lastrowid

        print(f"{request_id} Riot Account created. New account id id: {insert_id}")

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(f"Riot Account created: {insert_id}"),
        }

    except Exception as e:
        print(f"{request_id} Failed to create riot account, Error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps(f"Failed to create riot account, Error: {str(e)}"),
        }

    finally:
        if connection:
            connection.close()
