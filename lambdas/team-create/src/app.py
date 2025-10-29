import base64
import json
import os
import boto3
import pymysql
from datetime import datetime

s3 = boto3.client("s3")

INSERT_TEAMS_SQL = """
    INSERT INTO teams (name, logo_url, banner_url, tag)
    VALUES (%s, %s, %s, %s, %s)
"""

def validate_team_data(team_data) -> bool:
    if not all(team_data.get(field, "").strip() for field in ["name", "logo_bytes", "banner_bytes", "tag"]):
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

def upload_image(image_bytes,location) -> str | None:
    if not image_bytes:
        return None
    
    decoded_bytes = base64.b64decode(image_bytes)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    file_name = f"{location}/{timestamp}.png"

    s3.put_object(
        Bucket=os.environ["BUCKET_NAME"],
        Key=file_name,
        Body=decoded_bytes,
        ContentType="image/png"
    )

    return f"https://lockout.nemika.me/{file_name}"

def lambda_handler(event, context):
    request_id = context.aws_request_id

    team_data = json.loads(event["body"])

    if not validate_team_data(team_data):
        return {
            'statusCode': 400,
            'body': json.dumps("Invalid body data")
        }
    
    name = team_data.get("name")
    logo_bytes = team_data.get("logo_bytes")
    banner_bytes = team_data.get("banner_bytes")
    tag = team_data.get("tag")
    
    
    connection = None

    try:
        connection = create_connection()

        logo_url = upload_image(logo_bytes,"Logo")
        banner_url = upload_image(banner_bytes,"Banner")

        with connection.cursor() as cursor:
            cursor.execute(
                INSERT_TEAMS_SQL, 
                (name, logo_url, banner_url, tag)
            )
            connection.commit()
            insert_id = cursor.lastrowid

        return {    
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            "body": json.dumps(f"Team created: {insert_id}")
    }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps(f"Failed to create team, Error: {str(e)}")
        }

    finally:
        if connection:
            connection.close()
