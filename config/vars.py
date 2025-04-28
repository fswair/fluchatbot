import os
import json

import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

with open("./config/data/languages.json") as f:
    LANGS = json.load(f)

with open("./config/data/countries.json") as f:
    COUNTRIES = json.load(f)
