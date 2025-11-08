import base64
import json
import os
import pymysql
import logging
import requests
from datetime import datetime

RIOT_API_KEY = os.environ["RIOT_API_KEY"]
RIOT_PLATFORM = "euw1"

# change interval? change limit?
GET_PLAYER_UUIDS_SQL = """
    SELECT account_puuid FROM riot_accounts
    WHERE last_champion_mastery_fetch IS NULL 
        OR last_champion_mastery_fetch < NOW() - INTERVAL 1 WEEK
    ORDER BY last_champion_mastery_fetch IS NOT NULL, last_champion_mastery_fetch DESC
    LIMIT 5;
"""

INSERT_OR_UPDATE_MASTERY_SQL = """
    INSERT INTO account_champion_mastery (
        account_puuid,
        mastery_json
    ) VALUES (%s, %s)
    ON DUPLICATE KEY UPDATE
        mastery_json = VALUES(mastery_json);
"""

UPDATE_LAST_MASTERY_FETCH_SQL = """
    UPDATE riot_accounts
    SET last_champion_mastery_fetch = %s
    WHERE account_puuid = %s
"""

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def create_connection() -> pymysql.Connection:
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        cursorclass=pymysql.cursors.DictCursor
    )

def fetch_puuids() -> list[str]:
    connection = None
    try:
        connection = create_connection()
        with connection.cursor() as cursor:
            cursor.execute(GET_PLAYER_UUIDS_SQL)
            results = cursor.fetchall()
            puuids = [row['account_puuid'] for row in results]
            logger.info(f"Fetched {len(puuids)} PUUIDs from database.")
            return puuids
    except Exception as e: 
        logger.error(f"Error fetching PUUIDs: {str(e)}")
        return []
    finally:
        if connection:
            connection.close()
    
def update_mastery_timestamp(connection, puuid):
    with connection.cursor() as cursor:
        cursor.execute(UPDATE_LAST_MASTERY_FETCH_SQL, (datetime.now(), puuid))

def fetch_champion_mastery_from_riot(puuid: str) -> list[dict] | None:
    url = (
        f"https://{RIOT_PLATFORM}.api.riotgames.com/"
        f"lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}"
    )
    headers = {"X-Riot-Token": RIOT_API_KEY}

    logger.info(f"Fetching champion mastery for puuid={puuid} from {url}")
    resp = requests.get(url, headers=headers, timeout=10)

    # rate limit handling
    if resp.status_code == 429:
        retry_after = resp.headers.get("Retry-After", "1")
        logger.warning(
            f"Rate limited by Riot API when fetching mastery for {puuid}. "
            f"Retry after {retry_after}s. Stopping batch."
        )
        return None

    resp.raise_for_status()
    return resp.json()

def save_mastery_json(connection, puuid: str, mastery_json: list[dict]):
    with connection.cursor() as cursor:
        cursor.execute(
            INSERT_OR_UPDATE_MASTERY_SQL,
            (puuid, json.dumps(mastery_json)),
        )

def lambda_handler(event, context):
    puuids = fetch_puuids()
    if not puuids:
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"message": "No PUUIDs to process."}),
        }
    
    connection = create_connection()
    processed_accounts = 0

    try:
        for puuid in puuids:
            mastery_json = fetch_champion_mastery_from_riot(puuid)

            if mastery_json is None:
                break

            save_mastery_json(connection, puuid, mastery_json)
            update_mastery_timestamp(connection, puuid)
            processed_accounts += 1

        connection.commit()
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP error talking to Riot API: {e}")
        connection.rollback()
        return {
            "statusCode": 502,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"message": f"Error fetching from Riot API: {str(e)}"}),
        }
    except Exception as e:
        logger.error(f"Error saving champion mastery to DB: {e}")
        connection.rollback()
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"message": f"DB error: {str(e)}"}),
        }
    finally:
        connection.close()
    
    return {
        "statusCode": 201,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(
            {
                "message": "Champion mastery fetched and stored.",
                "accounts_processed": processed_accounts,
            }
        ),
    }