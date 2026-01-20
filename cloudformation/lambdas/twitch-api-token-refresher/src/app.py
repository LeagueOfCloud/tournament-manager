import os
import json
import requests
import boto3

TWITCH_TOKEN_URL = "https://id.twitch.tv/oauth2/token"

secrets_client = boto3.client("secretsmanager")


def lambda_handler(event, context):
    client_id = os.environ.get("TWITCH_CLIENT_ID")
    client_secret = os.environ.get("TWITCH_CLIENT_SECRET")
    secret_arn = os.environ.get("TWITCH_APP_SECRET_ARN")

    if not client_id or not client_secret or not secret_arn:
        raise ValueError("Missing required environment variables")

    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
    }

    try:
        # Request Twitch App Access Token
        response = requests.post(TWITCH_TOKEN_URL, data=payload, timeout=10)
        response.raise_for_status()

        data = response.json()

        access_token = data["access_token"]
        expires_in = data["expires_in"]
        token_type = data.get("token_type", "bearer")

        # Store token in Secrets Manager
        secret_value = {
            "access_token": access_token,
            "expires_in": expires_in,
            "token_type": token_type,
        }

        secrets_client.put_secret_value(
            SecretId=secret_arn, SecretString=json.dumps(secret_value)
        )

        print("Twitch App Access Token updated in Secrets Manager")

        return {
            "statusCode": 200,
            "body": {
                "message": "Token generated and stored successfully",
                "expires_in": expires_in,
            },
        }

    except requests.RequestException as e:
        print("HTTP error while requesting token:", str(e))
        raise

    except Exception as e:
        print("Unhandled error:", str(e))
        raise
