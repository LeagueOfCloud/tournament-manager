import base64
import json
import os
import boto3
import pymysql
from datetime import datetime

INSERT_TOURNAMENT_MATCH_SQL = """
    INSERT INTO tournament_matches (team_1_id, team_2_id, start_date)
    VALUES (%s, %s, %s)
"""

def validate_match_data(match_data) -> bool:
    if not all(match_data.get(field, "").strip()for field in ["team_1_id", "team_2_id", "start_date"]):
        return False
    
    try:
        int(match_data.get("team_1_id", ""))
        int(match_data.get("team_2_id", ""))
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
        cursorclass=pymysql.cursors.DictCursor
    )

def lambda_handler(event, context):
    request_id = context.aws_request_id

    match_data = json.loads(event["body"])

    if not validate_match_data(match_data):
        return {
            'statusCode': 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            'body': json.dumps("Invalid body data")
        }

    team_1_id = int(match_data.get("team_1_id"))
    team_2_id = int(match_data.get("team_2_id"))
    start_date = match_data.get("start_date")
    
    connection = None

    try:
        connection = create_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                INSERT_TOURNAMENT_MATCH_SQL, 
                (team_1_id, team_2_id, start_date)
            )
            connection.commit()
            insert_id = cursor.lastrowid

        return {    
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            "body": json.dumps({
                "message": "Tournament match was created successfully!",
                "match_id": int(insert_id)
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps(f"Failed to create tournament match, Error: {str(e)}")
        }

    finally:
        if connection:
            connection.close()