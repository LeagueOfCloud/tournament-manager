import base64
import json
import os
import boto3
import pymysql
from datetime import datetime

s3 = boto3.client("s3")


def validate_team_data(team_data) -> bool:
    if not team_data.get("team_id"):
        return False
    
    try:
        int(team_data.get("team_id"))
    except (ValueError, TypeError):
        return False
    
    updatable_fields = ["name", "logo_url", "banner_url", "tag"]
    if not any(field in team_data for field in updatable_fields):
        return False
    
    if "team_id" in team_data:
        try:
            int(team_data.get("team_id"))
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

def build_update_query(team_data):
    """Build dynamic UPDATE query based on provided fields"""
    update_fields = []
    values = []
    
    if "name" in team_data:
        update_fields.append("name = %s")
        values.append(team_data["name"].strip())
    
    if "logo_url" in team_data:
        update_fields.append("logo_url = %s")
        logo_url = upload_image(team_data["logo_url"],"Logo")
        values.append(logo_url)
    
    if "banner_url" in team_data:
        update_fields.append("banner_url = %s")
        banner_url = upload_image(team_data["banner_url"],"Banner")
        values.append(banner_url)
    
    if "tag" in team_data:
        update_fields.append("tag = %s")
        values.append(team_data["tag"])
    
    return update_fields, values

def lambda_handler(event, context):
    request_id = context.aws_request_id
    team_data = json.loads(event["body"])

    if not validate_team_data(team_data):   
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({"error": "Invalid team data"})
        }
    
    team_id = int(team_data.get("team_id"))
    
    connection = None

    try:   
        connection = create_connection()
        
        update_fields, values = build_update_query(team_data)        
        
        if not update_fields:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({"error": "No valid fields to update"})
            }
        
        values.append(team_id)
        
        update_sql = f"""
            UPDATE teams 
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
                'body': json.dumps({"error": f"team not found with id: {team_id}"})
            }

        return {    
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                "message": "Team updated successfully",
                "team_id": team_id
            })
        }

    except pymysql.IntegrityError as e:
        error_code = e.args[0]
        error_msg = str(e)
        
        if error_code == 1062:  
            if 'name' in error_msg:
                error_response = "A team with this name already exists"
            elif 'logo_url' in error_msg:
                error_response = "A team with this Logo URL already exists"
            elif 'banner_url' in error_msg:
                error_response = "A team with this Banner URL already exists"
            elif 'tag' in error_msg:
                error_response = "A team with this Tag already exists"
            else:
                error_response = "Duplicate entry detected"
        
        
        elif error_code == 1452:  
            if 'team_id' in error_msg:
                error_response = "Invalid team_id: team does not exist"

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
            "body": json.dumps({"error": f"Failed to update team: {str(e)}"})
        }

    finally:
        if connection:
            connection.close()