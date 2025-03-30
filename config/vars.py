import os
import json
import dotenv

dotenv.load_dotenv()

API_ID = os.environ.get("API_ID")
API_HASH =  os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

with open("./config/data/languages.json") as f:
    LANGS = json.load(f)

with open("./config/data/countries.json") as f:
    COUNTRIES = json.load(f)