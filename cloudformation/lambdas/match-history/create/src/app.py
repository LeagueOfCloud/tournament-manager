import base64
import json
import os
import boto3
import pymysql
import requests
import logging
from datetime import datetime

s3 = boto3.client("s3")

RIOT_API_KEY = os.environ["RIOT_API_KEY"]
REGION = "europe"
GET_PLAYER_UUIDS_SQL = """
SELECT account_puuid FROM riot_accounts
"""
INSERT_MATCH_HISTORY_SQL = """
    INSERT INTO match_history (match_id, match_data)
    VALUES (%s, %s)
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

def fetch_puuids() -> list:
    connection = None
    try:
        connection = create_connection()
        with connection.cursor() as cursor:
            cursor.execute(GET_PLAYER_UUIDS)
            results = cursor.fetchall()
            puuids = [row['account_puuid'] for row in results]
            logger.info(f"Fetched {len(puuids)} PUUIDs from database.")
            return puuids
    except Exception as e: 
        logger.error(f"Error fetching PUUIDs: {str(e)}")
        return []


def fetch_match_data(match_id: str) -> dict:
    puuids = fetch_puuids()
    for puuid in puuids:
        url = f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"
        headers = {"X-Riot-Token": RIOT_API_KEY}

        try:
            logger.info(f"Fetching match IDs for {puuid} from {url}")
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", "1")
                logger.warning(f"Rate limited by Riot API. Retry after {retry_after}s.")
                raise Exception(f"Rate limit exceeded. Retry after {retry_after} seconds.")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching match {match_id}: {str(e)}")
            raise


def lambda_handler(event, context):
    request_id = context.aws_request_id
    logger.info(f"Request ID: {request_id}")

    
    try:
        body = json.loads(event["body"])
        match_id = body.get("match_id")
    except Exception as e:
        logger.error(f"Invalid request body: {str(e)}")
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"message": "Invalid request body"})
        }

    if not match_id or not match_data:
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"message": "Invalid match data"})
        }
    try:
        match_data = fetch_match_data(match_id)
    except Exception as e:
        logger.error(f"Failed to fetch match {match_id}: {str(e)}")
        return {
            "statusCode": 502,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"message": f"Error fetching from Riot API: {str(e)}"})
        }

    encoded_match_data = base64.b64encode(json.dumps(match_data).encode("utf-8"))

    try:
        connection = create_connection()
        with connection.cursor() as cursor:
            cursor.execute(INSERT_MATCH_HISTORY_SQL, (match_id, encoded_match_data))
        connection.commit()
        logger.info(f"Match history for {match_id} inserted successfully.")
   
   
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"message": f"Database error: {str(e)}"})
        }
    finally:
        connection.close()

    return {
        "statusCode": 201,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps({"message": "Match history created successfully", "match_id": match_id})
    }

def validate_match_data(match_data: dict) -> bool:
    if not match_data:
        return False
    if "match_id" not in match_data:
        return False
    return True