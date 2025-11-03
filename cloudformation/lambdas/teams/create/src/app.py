import base64
import json
import os
import boto3
import pymysql
from datetime import datetime

s3 = boto3.client("s3")

INSERT_TEAMS_SQL = """
    INSERT INTO teams (name, logo_url, banner_url, tag)
    VALUES (%s, %s, %s, %s)
"""

def validate_team_data(team_data) -> bool:
    if not all(team_data.get(field, "").strip() for field in ["name", "tag"]):
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

def generate_image_upload_url(location, max_size_mb = 5) -> str | None:
    max_size_bytes = max_size_mb * 1024 * 1024
    timestamp = datetime.now().timestamp()
    file_name = f"{location}/{timestamp}.png"

    post = s3.generate_presigned_post(
        Bucket=bucket,
        Key=file_name,
        Fields={"Content-Type": "png"},
        Conditions=[
            ["content-length-range", 0, max_size_bytes],
            {"Content-Type": "png"}
        ],
        ExpiresIn=300
    )

    upload_url = post["url"]

    return (f"https://lockout.nemika.me/{file_name}", upload_url)

def lambda_handler(event, context):
    request_id = context.aws_request_id

    team_data = json.loads(event["body"])

    if not validate_team_data(team_data):
        return {
            'statusCode': 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            'body': json.dumps("Invalid body data")
        }
    
    name = team_data.get("name")
    tag = team_data.get("tag")
    
    connection = None

    try:
        connection = create_connection()

        [logo_url, logo_upload_url] = generate_image_upload_url("teams/logo", 15)
        [banner_url, banner_upload_url] = generate_image_upload_url("teams/banner", 50)

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
            "body": json.dumps({
                "message": "Team was created successfully!",
                "new_team_id": int(insert_id),
                "logo_upload_url": logo_upload_url,
                "banner_upload_url": banner_upload_url
            })
    }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps(f"Failed to create team, Error: {str(e)}")
        }

    finally:
        if connection:
            connection.close()
