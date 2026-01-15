import json
import os
import pymysql
import logging
import traceback
import requests

RIOT_API_KEY = os.environ["RIOT_API_KEY"]
REGION = "europe"
connection = None
match_data_url = f"https://{REGION}.api.riotgames.com/lol/match/v5/matches"
logger = logging.getLogger()
logger.setLevel(logging.INFO)

GET_MATCH_IDS_SQL = """
    SELECT match_id
    FROM match_history
    WHERE match_data IS NULL
    LIMIT 5;
"""

UPDATE_MATCH_HISTORY_SQL = """
    UPDATE match_history
    SET match_data = %s
    WHERE match_id = %s;
"""


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


def fetch_match_ids() -> list:
    connection = get_connection()
    match_ids = []
    try:
        with connection.cursor() as cursor:
            cursor.execute(GET_MATCH_IDS_SQL)
            results = cursor.fetchall()
            match_ids = [row["match_id"] for row in results]
            logger.info(f"Fetched {len(match_ids)} matches from database.")
    except Exception as e:
        logger.error(traceback.format_exc())
        logger.error(f"Error fetching match_ids: {str(e)}")
    return match_ids


def fetch_match_data(match_id):
    url = f"{match_data_url}/{match_id}"
    headers = {"X-Riot-Token": RIOT_API_KEY}
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 429:
        logger.warning("Rate limited by Riot API.")
        raise Exception("Rate limited by Riot API.")
    response.raise_for_status()
    return response.json()


def update_match_data(match_id, match_data):
    connection = get_connection()
    match_data_json = json.dumps(match_data)
    try:
        with connection.cursor() as cursor:
            cursor.execute(UPDATE_MATCH_HISTORY_SQL, (match_data_json, match_id))
            logger.info(f"Updated {match_id} with match_data in database.")
        connection.commit()
    except Exception as e:
        logger.error(traceback.format_exc())
        logger.error(f"Error fetching match_ids: {str(e)}")


def close_connection():
    connection = get_connection()
    if connection:
        connection.close()
    connection = None


def lambda_handler(event, context):
    match_ids = fetch_match_ids()

    for match_id in match_ids:
        try:
            match_data = fetch_match_data(match_id)
            update_match_data(match_id, match_data)
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(
                f"Error fetching match_data for Match ID: {match_id}, error: {str(e)}"
            )
            close_connection()
            return {
                "statusCode": 500,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
            }

    close_connection()

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
    }
