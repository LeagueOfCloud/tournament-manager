import json
import os
import pymysql
import logging
import requests
from datetime import datetime

RIOT_API_KEY = os.environ["RIOT_API_KEY"]
region = "EUW1"
connection = None
league_entries_url = (
    f"https://{region}.api.riotgames.com/lol/league/v4/entries/by-puuid"
)
logger = logging.getLogger()

GET_PLAYER_UUIDS_SQL = """
    SELECT account_puuid
    FROM riot_accounts
    WHERE last_player_stats_fetch IS NULL
        OR last_player_stats_fetch < NOW() - INTERVAL 1 DAY
    ORDER BY last_player_stats_fetch IS NOT NULL, last_player_stats_fetch DESC
    LIMIT 5;
"""

UPSERT_PLAYER_STATS_SQL = """
    INSERT INTO player_stats (puuid, league_entries)
    VALUES (%s, %s)
    ON DUPLICATE KEY UPDATE
        league_entries = VALUES(league_entries);
"""

UPDATE_LAST_PLAYER_STATS_FETCH_SQL = """
    UPDATE riot_accounts
    SET last_player_stats_fetch = %s
    WHERE account_puuid = %s
"""


def fetch_puuids() -> list:
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute(GET_PLAYER_UUIDS_SQL)
            results = cursor.fetchall()
            puuids = [row["account_puuid"] for row in results]
            return puuids
    except Exception as e:
        logger.error(f"Error fetching PUUIDs: {str(e)}")
        return []


def get_connection() -> pymysql.Connection:
    global connection
    if connection is None:
        connection = pymysql.connect(
            host=os.environ["DB_HOST"],
            port=int(os.environ["DB_PORT"]),
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            database=os.environ["DB_NAME"],
            cursorclass=pymysql.cursors.DictCursor,
        )
    return connection


def fetch_league_entries(puuid):
    url = f"{league_entries_url}/{puuid}"
    headers = {"X-Riot-Token": RIOT_API_KEY}
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 429:
        logger.warning("Rate limited by Riot API.")
        raise Exception("Rate limited by Riot API.")
    response.raise_for_status()
    return response.json()


def save_player_stats(puuid, league_entries):
    connection = get_connection()
    league_entries_json = json.dumps(league_entries)
    try:
        with connection.cursor() as cursor:
            cursor.execute(UPSERT_PLAYER_STATS_SQL, (puuid, league_entries_json))
            cursor.execute(UPDATE_LAST_PLAYER_STATS_FETCH_SQL, (datetime.now(), puuid))
        connection.commit()
    except Exception as e:
        logger.error(f"Error fetching match_ids: {str(e)}")


def lambda_handler(event, context):
    puuids = fetch_puuids()
    for puuid in puuids:
        try:
            league_entries = fetch_league_entries(puuid)
            save_player_stats(puuid, league_entries)
        except Exception as e:
            logger.error(
                f"Error fetching league_entries for puuid: {puuid}, error: {str(e)}"
            )

            if connection:
                connection.close()

            return {
                "statusCode": 500,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
            }

    if connection:
        connection.close()

    return {
        "statusCode": 201,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
    }
