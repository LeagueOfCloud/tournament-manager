import base64
import json
import os
import boto3
import pymysql
import requests
import logging
import datetime
import traceback

s3 = boto3.client("s3")

RIOT_API_KEY = os.environ["RIOT_API_KEY"]
REGION = "europe"
GET_PLAYER_UUIDS_SQL = """
SELECT account_puuid
FROM riot_accounts
WHERE last_match_history_fetch IS NULL
    OR last_match_history_fetch < NOW() - INTERVAL 1 DAY
ORDER BY last_match_history_fetch IS NOT NULL, last_match_history_fetch DESC
LIMIT 5;
"""
INSERT_MATCH_HISTORY_SQL = """
    INSERT INTO match_history (match_id)
    VALUES (%s)
"""
UPDATE_LAST_MATCH_HISTORY_FETCH_SQL = """
UPDATE riot_accounts
SET last_match_history_fetch = %s
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
        cursorclass=pymysql.cursors.DictCursor,
    )


def fetch_puuids() -> list:
    connection = None
    try:
        connection = create_connection()
        with connection.cursor() as cursor:
            cursor.execute(GET_PLAYER_UUIDS_SQL)
            results = cursor.fetchall()
            puuids = [row["account_puuid"] for row in results]
            return puuids
    except Exception as e:
        logger.error(f"Error fetching PUUIDs: {str(e)}")
        return []
    finally:
        if connection:
            connection.close()


def update_timestamp(puuid):
    connection = create_connection()
    with connection.cursor() as cursor:
        cursor.execute(
            UPDATE_LAST_MATCH_HISTORY_FETCH_SQL, (datetime.datetime.now(), puuid)
        )
    connection.commit()
    connection.close()


def fetch_queue_type(puuid, queue_id) -> list:
    two_weeks_ago = datetime.datetime.now() - datetime.timedelta(weeks=2)
    start_time_epoch = int(two_weeks_ago.timestamp())
    match_ids = []
    url = f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?startTime={start_time_epoch}&queue={queue_id}"
    headers = {"X-Riot-Token": RIOT_API_KEY}

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After", "1")
            logger.warning(f"Rate limited by Riot API. Retry after {retry_after}s.")
            return match_ids
        update_timestamp(puuid)

        response.raise_for_status()
        match_ids += response.json()
        return match_ids

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching match Match ID: {str(e)}")
        return match_ids


def fetch_match_ids() -> list:
    puuids = fetch_puuids()
    match_ids = []

    for puuid in puuids:
        match_ids += fetch_queue_type(puuid, 420)  # Ranked Solo/Duo
        if len(match_ids) < 20:
            match_ids += fetch_queue_type(puuid, 440)  # Ranked Flex
        if len(match_ids) < 20:
            match_ids += fetch_queue_type(puuid, 400)  # Normal Draft
    return match_ids


def lambda_handler(event, context):
    request_id = context.aws_request_id
    try:
        match_ids = fetch_match_ids()
    except Exception as e:
        logger.error(f"Failed to fetch match IDs: {str(e)}")
        return {
            "statusCode": 502,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"message": f"Error fetching from Riot API: {str(e)}"}),
        }

    try:
        connection = create_connection()

        for match_id in match_ids:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(INSERT_MATCH_HISTORY_SQL, (match_id))
                connection.commit()

            except Exception as e:
                error_code = e.args[0]
                if error_code == 1062:
                    pass  # Duplicate entry, ignore
                else:
                    logger.error(
                        f"Could not insert match_id {match_id} to the database: {e}"
                    )
    except Exception as e:
        traceback.print_exc()
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"message": f"Failed to get match IDs: {e}"}),
        }

    finally:
        if connection:
            connection.close()

    return {
        "statusCode": 201,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
    }
