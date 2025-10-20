import json,os
from datetime import datetime
from pathlib import Path
from fastapi.encoders import jsonable_encoder

CREDENTIALS_FILE = "tokens/angelone-credentials.json"

def save_token(broker_name: str, token_data: dict):
    os.makedirs("tokens", exist_ok=True)  
    Path("tokens").mkdir(exist_ok=True)
    safe_data = jsonable_encoder(token_data)
    with open(f"tokens/{broker_name}_token.json", "w") as f:
        json.dump(safe_data, f, indent=4)

def load_token(broker_name: str):
    try:
        with open(f"tokens/{broker_name}_token.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
def save_credentials(broker_name, creds):
    data = {}
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r") as f:
            data = json.load(f)
    data[broker_name] = creds
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(data, f)


def load_credentials(broker_name):
    if not os.path.exists(CREDENTIALS_FILE):
        return None
    with open(CREDENTIALS_FILE, "r") as f:
        data = json.load(f)
    return data.get(broker_name)
