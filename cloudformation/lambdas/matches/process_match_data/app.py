import json
import os
import pymysql
import logging
import requests

connection = None
logger = logging.getLogger()
logger.setLevel(logging.INFO)

GET_MATCH_IDS_SQL = """
    SELECT match_id, match_data
    FROM match_history
    WHERE match_data IS NOT NULL AND was_processed = 'false'
    LIMIT 1;
"""

MARK_MATCH_PROCESSED_SQL = """
    UPDATE match_history
    SET was_processed = 'true'
    WHERE match_id = %s;
"""

INSERT_PROCESSED_MATCH_DATA_SQL = """
    INSERT INTO processed_match_data (match_id, account_id, account_name, champion_name, teamPosition, goldEarned, totalDamageDealtToChampions, totalMinionsKilled, kills, deaths, assists, vision_score, win, queueId, gameDuration)
    VALUES
        (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    
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
            cursorclass=pymysql.cursors.DictCursor
        )
    return connection

def fetch_match_ids() -> list:
    connection = get_connection()
    match_ids = []
    try:
        with connection.cursor() as cursor:
            cursor.execute(GET_MATCH_IDS_SQL)
            results = cursor.fetchall()
            match_ids = [row['match_id'] for row in results]
            match_data = [row['match_data'] for row in results]
            logger.info(f"Fetched {len(match_ids)} matches and their data from database.")
    except Exception as e: 
        logger.error(f"Error fetching match_ids: {str(e)}")
    return match_ids

def update_match_data(match_id, match_data):
    connection = get_connection()
    match_data_json = json.dumps(match_data)
    try:
        with connection.cursor() as cursor:
            cursor.execute(INSERT_PROCESSED_MATCH_DATA_SQL, (match_data_json, match_id))
            logger.info(f"Updated {match_id} with match_data in database.")
        connection.commit()
    except Exception as e: 
        logger.error(f"Error fetching match_ids: {str(e)}")

def close_connection():
    connection = get_connection()
    connection.close()
    connection = None

def lambda_handler(event, context):
    match_ids = fetch_match_ids()

    for match_id in match_ids:
        try:
            match_data = fetch_match_data(match_id)
            update_match_data(match_id, match_data)
        except Exception as e:
            logger.error(f"Error fetching match_data for Match ID: {match_id}, error: {str(e)}")
            return {
                "statusCode": 500,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },    
            }

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },    
    }
