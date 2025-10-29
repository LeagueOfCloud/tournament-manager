import base64
import json
import os
import boto3
import pymysql
from datetime import datetime

s3 = boto3.client("s3")

INSERT_PLAYER_SQL = """
    INSERT INTO players (name, avatar_url, discord_id, team_id, team_role)
    VALUES (%s, %s, %s, %s, %s)
"""

def validate_player_data(player_data) -> bool:
    if not all(player_data.get(field, "").strip() for field in ["name", "discord_id", "team_role"]):
        return False
    
    try:
        int(player_data.get("team_id", ""))
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

def upload_avatar(avatar_bytes) -> str | None:
    if not avatar_bytes:
        return None
    
    decoded_bytes = base64.b64decode(avatar_bytes)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    file_name = f"avatars/{timestamp}.png"

    s3.put_object(
        Bucket=os.environ["BUCKET_NAME"],
        Key=file_name,
        Body=decoded_bytes,
        ContentType="image/png"
    )

    return f"https://lockout.nemika.me/{file_name}"

def lambda_handler(event, context):
    request_id = context.aws_request_id

    player_data = json.loads(event["body"])

    if not validate_player_data(player_data):
        return {
            'statusCode': 400,
            'body': json.dumps("Invalid body data")
        }
    
    name = player_data.get("name")
    avatar_bytes = player_data.get("avatar_bytes", "")
    discord_id = player_data.get("discord_id")
    team_id = int(player_data.get("team_id"))
    team_role = player_data.get("team_role")
    
    connection = None

    try:
        connection = create_connection()

        avatar_url = upload_avatar(avatar_bytes)

        with connection.cursor() as cursor:
            cursor.execute(
                INSERT_PLAYER_SQL, 
                (name, avatar_url, discord_id, team_id, team_role)
            )
            connection.commit()
            insert_id = cursor.lastrowid

        return {    
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            "body": json.dumps(f"Player created: {insert_id}")
    }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps(f"Failed to create player, Error: {str(e)}")
        }

    finally:
        if connection:
            connection.close()
