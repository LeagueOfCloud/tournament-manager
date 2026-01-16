import base64
import json
import os
import boto3
import pymysql
from datetime import datetime


def create_connection() -> pymysql.Connection:
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        cursorclass=pymysql.cursors.DictCursor,
    )


def validate_match_data(match_data) -> bool:
    try:
        int(match_data.get("id", ""))
        team_1_id = int(match_data.get("team_1_id", ""))
        team_2_id = int(match_data.get("team_2_id", ""))
        int(match_data.get("date", ""))
        if team_1_id == team_2_id:
            return False
    except (ValueError, TypeError):
        return False

    return True


def lambda_handler(event, context):
    request_id = context.aws_request_id
    match_data = json.loads(event["body"])

    if not validate_match_data(match_data):
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps("Invalid match data"),
        }

    id = int(match_data.get("id"))
    team_1_id = int(match_data.get("team_1_id"))
    team_2_id = int(match_data.get("team_2_id"))
    start_date = int(match_data.get("date"))
    start_date_date = datetime.fromtimestamp(start_date / 1000)
    vod_url = match_data.get("vod_url")

    connection = None
    try:
        connection = create_connection()

        with connection.cursor() as cursor:
            rows_affected = cursor.execute(
                "UPDATE tournament_matches SET team_1_id=%s, team_2_id=%s, start_date=%s, vod_url=%s WHERE id=%s",
                (team_1_id, team_2_id, start_date_date, vod_url, id),
            )
            connection.commit()

        if rows_affected == 0:
            return {
                "statusCode": 404,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                "body": json.dumps({"error": f"Match not found with id: {id}"}),
            }

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps("Tournament match updated successfully"),
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(f"Failed to update tournament match, Error: {str(e)}"),
        }
    finally:
        if connection:
            connection.close()
