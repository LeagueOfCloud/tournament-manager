import json
import os
import boto3
import pymysql

# s3_client = boto3.client("s3")

# SQL query
INSERT_PLAYER_SQL = """
    INSERT INTO players (name, avatar_url, discord_id, team_id, team_role)
    VALUES (%s, %s, %s, %s, %s)
"""

def lambda_handler(event, context):
    # TODO: Validation on these
    name = event.get("name")
    avatar_bytes = event.get("avatar_bytes")
    discord_id = event.get("discord_id")
    team_id = event.get("team_id")
    team_role = event.get("team_role")

    connection = None

    try:
        connection = pymysql.connect(
            host=os.environ["DB_HOST"],
            port=int(os.environ["DB_PORT"]),
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            database=os.environ["DB_NAME"],
            cursorclass=pymysql.cursors.DictCursor
        )

        # TODO: Properly handle file bytes
        file_name = f"avatars/{name}.txt"
        # s3_client.put_object(
        #     Bucket=os.environ["BUCKET_NAME"],
        #     Key=file_name,
        #     Body=avatar_bytes
        # )

        avatar_url = f"https://lockout.nemika.me/{file_name}"

        with connection.cursor() as cursor:
            cursor.execute(INSERT_PLAYER_SQL, (name, avatar_url, discord_id, team_id, team_role))
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
        print(f"Failed to create player: {name}, Error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps(f"Failed to create player: {name}, Error: {str(e)}")
        }

    finally:
        if connection:
            connection.close()
