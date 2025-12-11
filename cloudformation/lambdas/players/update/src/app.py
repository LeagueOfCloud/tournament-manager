import base64
import json
import os
import boto3
import pymysql
from datetime import datetime

s3 = boto3.client("s3")

VALID_TEAM_ROLES = ['top', 'jungle', 'mid', 'bot', 'support', 'sub']

def validate_player_data(player_data) -> bool:
    if not player_data.get("player_id"):
        return False
    
    try:
        int(player_data.get("player_id"))
    except (ValueError, TypeError):
        return False
    
    updatable_fields = ["name", "discord_id", "team_role", "team_id"]
    if not any(field in player_data for field in updatable_fields):
        return False
    
    if "team_id" in player_data:
        try:
            int(player_data.get("team_id"))
        except (ValueError, TypeError):
            return False
    
    if "team_role" in player_data:
        if player_data["team_role"] not in VALID_TEAM_ROLES:
            return False
    
    for field in ["name", "discord_id"]:
        if field in player_data and not player_data[field].strip():
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

    presigned_data = s3.generate_presigned_post(
        Bucket=os.environ["BUCKET_NAME"],
        Key=file_name,
        Fields={"Content-Type": "png"},
        Conditions=[
            ["content-length-range", 0, max_size_bytes],
            {"Content-Type": "png"}
        ],
        ExpiresIn=300
    )

    return (f"https://lockout.nemika.me/{file_name}", presigned_data)

def build_update_query(player_data):
    """Build dynamic UPDATE query based on provided fields"""
    update_fields = []
    values = []
    
    if "name" in player_data:
        update_fields.append("name = %s")
        values.append(player_data["name"].strip())
    
    if "discord_id" in player_data:
        update_fields.append("discord_id = %s")
        values.append(player_data["discord_id"].strip())
    
    if "team_id" in player_data:
        update_fields.append("team_id = %s")
        values.append(int(player_data["team_id"]))

    if "avatar_url" in player_data:
        update_fields.append("avatar_url = %s")
        values.append(player_data["avatar_url"])
    
    if "team_role" in player_data:
        update_fields.append("team_role = %s")
        values.append(player_data["team_role"])
    
    if "cost" in player_data:
        update_fields.append("cost = %s")
        values.append(player_data["cost"])
    return update_fields, values

def lambda_handler(event, context):
    request_id = context.aws_request_id
    player_data = json.loads(event["body"])

    if not validate_player_data(player_data):   
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({"error": "Invalid player data"})
        }
    
    player_id = int(player_data.get("player_id"))
    
    connection = None

    try:   
        connection = create_connection()

        upload_data = {}

        if player_data.get("new_avatar"):
            [avatar_url, avatar_upload_presigned_data] = generate_image_upload_url("avatars", 10)
            upload_data["avatar_presigned_data"] = avatar_upload_presigned_data
            player_data["avatar_url"] = avatar_url
        
        update_fields, values = build_update_query(player_data)
        
        if not update_fields:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({"error": "No valid fields to update"})
            }
        
        values.append(player_id)
        
        update_sql = f"""
            UPDATE players 
            SET {', '.join(update_fields)}
            WHERE id = %s
        """

        with connection.cursor() as cursor:
            rows_affected = cursor.execute(update_sql, values)
            connection.commit()
        
        if rows_affected == 0:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({"error": f"Player not found with id: {player_id}"})
            }

        return {    
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                "message": "Player updated successfully",
                "player_id": player_id,
                "upload": upload_data
            })
        }

    except pymysql.IntegrityError as e:
        error_code = e.args[0]
        error_msg = str(e)
        
        if error_code == 1062:  
            if 'name' in error_msg:
                error_response = "A player with this name already exists"
            elif 'discord_id' in error_msg:
                error_response = "A player with this Discord ID already exists"
            else:
                error_response = "Duplicate entry detected"
        elif error_code == 1452:  
            if 'team_id' in error_msg:
                error_response = "Invalid team_id: team does not exist"
            elif 'discord_id' in error_msg:
                error_response = "Invalid discord_id: profile does not exist"
            else:
                error_response = "Foreign key constraint violation"
        else:
            error_response = f"Database constraint violation: {error_msg}"
        
        return {
            "statusCode": 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            "body": json.dumps({"error": error_response})
        }
    
    except Exception as e:
        return {
            "statusCode": 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            "body": json.dumps({"error": f"Failed to update player: {str(e)}"})
        }

    finally:
        if connection:
            connection.close()
