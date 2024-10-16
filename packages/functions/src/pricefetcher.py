import os
import json
import boto3
import requests
from datetime import datetime
from decimal import Decimal

# Initialize DynamoDB client
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])
latest_update_table = dynamodb.Table(os.environ["LATEST_UPDATE_TABLE_NAME"])
api_key = os.environ["API_KEY"]

# CoinGecko API endpoint
COINGECKO_API = "https://api.coingecko.com/api/v3/coins/markets"


def update_latest_timestamp(timestamp):
    latest_update_table.put_item(Item={"id": "latest_update", "time": timestamp})


def handler(event, context):
    try:
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 250,  # Adjust as needed
            "page": 1,
            "sparkline": False,
        }
        headers = {
            "accept": "application/json",
            "x-cg-demo-api-key": api_key,
        }
        response = requests.get(COINGECKO_API, params=params, headers=headers)
        response.raise_for_status()
        coins = response.json()

        # Current timestamp
        now = datetime.utcnow()

        print(f"Processing {len(coins)} coins")

        update_latest_timestamp(int(now.timestamp()))

        # Process and store data
        with table.batch_writer() as batch:
            for coin in coins:
                print(f"Processing {coin['id']}")
                print(f"Price: {coin['current_price']}")
                print(f"Market Cap: {coin['market_cap']}")
                item = {
                    "pair": f"{coin["id"]}/usd",
                    "time": int(now.timestamp()),
                    "value": coin["current_price"],
                }
                item = json.loads(json.dumps(item), parse_float=Decimal)
                batch.put_item(Item=item)

        return {
            "statusCode": 200,
            "body": json.dumps(f"Successfully processed {len(coins)} coins"),
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"statusCode": 500, "body": json.dumps(f"Error: {str(e)}")}
