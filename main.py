from pyrogram import Client, StopPropagation, filters, idle
from pyrogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from config.vars import API_HASH, API_ID, BOT_TOKEN, LANGS, COUNTRIES
from pyromod import listen
from database import preferences, addresses
from utils import get_location, checker, fetcher, Match
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from logging import StreamHandler, getLogger, basicConfig, ERROR

import tgcrypto
import os
import asyncio
import random

os.mkdir("logs")

WORKDIR = "sessions"
APPNAME = "fluchatbot"
LOGPATH = "logs/general.log"
LOGNAME = "errors"

basicConfig(
    filename=LOGPATH,
    level=ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = getLogger(LOGNAME)
logger.setLevel(ERROR)
logger.addHandler(StreamHandler())

app = Client(
    name=APPNAME,
    workdir=WORKDIR,
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

def make_keyboard(criteria: int | str | None, main_keyboard: list[KeyboardButton] = None, is_key: bool = False, data: dict = {}, **kwargs) -> ReplyKeyboardMarkup:
    if main_keyboard and isinstance(main_keyboard, list) and isinstance(main_keyboard[0], list):
        buttons = []
        buttons.extend(main_keyboard)
        if criteria:
            buttons.insert(0, [KeyboardButton(criteria if not is_key else data.get(criteria, criteria))])
        return ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True, **kwargs)
    buttons = [main_keyboard]
    if criteria:
        buttons.insert(0, [KeyboardButton(criteria if not is_key else data.get(criteria, criteria))])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True, **kwargs)

@app.on_message(filters.command("start"))
async def start(c: Client, m: Message):
    user_lang = fetcher.get_user_lang(m.from_user.id)
    data = LANGS[user_lang or "english"]
    if not user_lang:
        await m.reply_text("Hello, it is fluchatbot bot. Before searching for matches please select a language...", reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("🇹🇷 Turkish"),
            KeyboardButton("🇬🇧 English")
            ],], resize_keyboard=True, one_time_keyboard=True
        ))
    else:
        if not checker.terms_accepted(m.from_user.id):
            return await m.reply_text(data["user_aggrement"], reply_markup=ReplyKeyboardMarkup([[KeyboardButton(data["accept"])]], resize_keyboard=True, one_time_keyboard=True))
        if not checker.has_preference(m.from_user.id):
            return await m.reply_text(data["profile_not_set"], reply_markup=ReplyKeyboardMarkup([[KeyboardButton(data["edit_profile"])]], resize_keyboard=True, one_time_keyboard=True))
        await m.reply_text(data["start_text"], reply_markup=ReplyKeyboardMarkup([[KeyboardButton(data["continue"])]], resize_keyboard=True, one_time_keyboard=True))
    raise StopPropagation
    
@app.on_message(filters.regex("(🇹🇷|🇬🇧).(Turkish|English)"))
async def reply_keyboard(c: Client, m: Message):
    _, lang = m.matches[0].groups()
    data = LANGS[lang.lower()]
    if checker.has_preference(m.from_user.id):
        preferences.updateByQuery({"user_id": m.from_user.id}, {"lang": lang.lower()})
    else:
        preferences.add({
            "user_id": m.from_user.id,
            "name": "",
            "lang": lang.lower(),
            "gender": "",
            "age": 0,
            "location": "",
            "preffered_gender": "",
            "preffered_age_range": "",
            "instagram": "",
            "phone": "",
            "search_status": 0,
            "current_chat": 0,
            "terms_accepted": 0
        })
    if checker.has_preference(m.from_user.id):
        await m.reply_text(data["language_selected"], reply_markup=ReplyKeyboardMarkup([
        [KeyboardButton(data["lets_start"]),
        ],], resize_keyboard=True, one_time_keyboard=True
    ))
    else:
        await m.reply_text(data["language_not_selected"])
    raise StopPropagation

@app.on_message(filters.regex("^(Lets start|Hadi başlayalım)!$"))
async def lets_start(c: Client, m: Message):
    data = LANGS[fetcher.get_user_lang(m.from_user.id) or "english"]
    if not checker.terms_accepted(m.from_user.id):
        return await m.reply_text(data["user_aggrement"], reply_markup=ReplyKeyboardMarkup([[KeyboardButton(data["accept"])]], resize_keyboard=True, one_time_keyboard=True))
    await m.reply_text(data["welcome"], reply_markup=ReplyKeyboardMarkup([[KeyboardButton(data["continue"])]], resize_keyboard=True, one_time_keyboard=True))
    raise StopPropagation

@app.on_message(filters.regex("^(Onaylıyorum|Accept)!$"))
async def accept(c: Client, m: Message):
    preferences.updateByQuery({"user_id": m.from_user.id}, {"terms_accepted": 1})
    data = LANGS[fetcher.get_user_lang(m.from_user.id) or "english"]
    await m.reply_text(data["welcome"], reply_markup=ReplyKeyboardMarkup([[KeyboardButton(data["continue"])]], resize_keyboard=True, one_time_keyboard=True))
    raise StopPropagation

@app.on_message(filters.regex("^(Edit Profile|Profili Düzenle)$"))
async def edit_profile(c: Client, m: Message):
    user_lang = fetcher.get_user_lang(m.from_user.id)
    data = LANGS[user_lang or "english"]
    preference = fetcher.get_preference(m.from_user.id)
    try:
        name_ask: Message = await c.ask(m.chat.id, data["ask_name"], timeout=60, reply_markup=make_keyboard(preference.name, [KeyboardButton(f"{data['keep']} {m.from_user.first_name}")]))
        name = name_ask.text.removeprefix(f"{data['keep']} ")
        preferences.updateByQuery({"user_id": m.from_user.id}, {"name": name})
    except asyncio.TimeoutError:
        return await m.reply_text(data["timeout"])
    except Exception as e:
        return logger.error(f"Error in user input: {e}")
    
    try
        age_ask: Message = await c.ask(m.chat.id, data["ask_age"], reply_markup=ReplyKeyboardRemove(), timeout=60)
        age = age_ask.text.strip()
        if not age.isdigit():
            return await m.reply_text(data["invalid_age"])
        age = int(age)
        if age < 18:
            return await m.reply_text(data["minimum_age"])
        preferences.updateByQuery({"user_id": m.from_user.id}, {"age": age})
    except asyncio.TimeoutError:
        return await m.reply_text(data["timeout"])
    except Exception as e:
        return logger.error(f"Error in user input: {e}")

    try:
        current_location = fetcher.get_address(m.from_user.id)
        current_country = getattr(current_location, "country", None)
        location_ask: Message = await c.ask(m.chat.id, data["ask_location"], timeout=60, reply_markup=make_keyboard(current_country, [[KeyboardButton(data["send_location"])], [KeyboardButton(data["keep_current_country"])] if not checker.has_address(m.from_user.id) else []]))
        location = getattr(location_ask, "location", None)
        if location_ask.text in (data["keep_current_country"], current_country):
            langcode = m.from_user.language_code.upper()
            location = langcode, COUNTRIES[langcode]
        if not location:
            return await m.reply_text(data["invalid_location"])
        if hasattr(location, "latitude") and hasattr(location, "longitude"):
            location_info = get_location(location.longitude, location.latitude)
            extra = f'H={location_info["address"].get("house_number", "none")};R={location_info["address"].get("road", "none")}'
            new_loc = dict(city=location_info["address"].get("city") or location_info["address"].get("province"), country=location_info["address"]["country"], country_code=location_info["address"]["country_code"], postcode=location_info["address"]["postcode"], display_name=location_info["display_name"], longitude=float(location.longitude), latitude=float(location.latitude), extra=extra)
        else:
            new_loc = dict(city="", country=location[1], country_code=location[0], postcode="", display_name="", longitude=0.0, latitude=0.0, extra="H=none;R=none")
        if not checker.has_address(m.from_user.id):
            addresses.add({"user_id": m.from_user.id, **new_loc})
        else:
            addresses.updateByQuery({"user_id": m.from_user.id}, {"user_id": m.from_user.id, **new_loc})
        
    except asyncio.TimeoutError:
        return await m.reply_text(data["timeout"])
    except Exception as e:
        return logger.error(f"Error in user input: {e}")

    try:
        gender_ask: Message = await c.ask(m.chat.id, data["ask_gender"], timeout=60, reply_markup=make_keyboard(preference.gender, [KeyboardButton(f"🚹 {data['male']}"), KeyboardButton(f"🚺 {data['female']}"), KeyboardButton(f"🏳️‍🌈 {data['other_gender']}")], is_key = True, data=data))
        gender = gender_ask.text.split()[-1].lower()
        if gender in LANGS["couples"]["female"]:
            gender = "female"
        elif gender in LANGS["couples"]["male"]:
            gender = "male"
        else:
            gender = "other"
        preferences.updateByQuery({"user_id": m.from_user.id}, {"gender": gender})
    except asyncio.TimeoutError:
        return await m.reply_text(data["timeout"])
    except Exception as e:
        return logger.error(f"Error in user input: {e}")

    try:
        preffered_gender_ask: Message = await c.ask(m.chat.id, data["ask_preffered_gender"], timeout=60, reply_markup=make_keyboard(preference.preffered_gender, [KeyboardButton(f"🚹 {data['male']}"), KeyboardButton(f"🚺 {data['female']}")], is_key=True, data=data))
        preffered_gender = preffered_gender_ask.text.split()[-1].lower()
        if preffered_gender in LANGS["couples"]["female"]:
            preffered_gender = "female"
        elif preffered_gender in LANGS["couples"]["male"]:
            preffered_gender = "male"
        else:
            preffered_gender = "other"
        preferences.updateByQuery({"user_id": m.from_user.id}, {"preffered_gender": preffered_gender})
    except asyncio.TimeoutError:
        return await m.reply_text(data["timeout"])
    except Exception as e:
        return logger.error(f"Error in user input: {e}")

    try:
        preffered_age_range_ask: Message = await c.ask(m.chat.id, data["ask_preffered_age"], timeout=60, reply_markup=make_keyboard(preference.preffered_age_range, [KeyboardButton("18-25"), KeyboardButton("25-35"), KeyboardButton("35-45"), KeyboardButton("45-60"), KeyboardButton("60-75"), KeyboardButton("75+")]))
        preffered_age_range = preffered_age_range_ask.text
        preferences.updateByQuery({"user_id": m.from_user.id}, {"preffered_age_range": preffered_age_range})
    except asyncio.TimeoutError:
        return await m.reply_text(data["timeout"])
    except Exception as e:
        return logger.error(f"Error in user input: {e}")

    try:
        instagram_ask: Message = await c.ask(m.chat.id, data["ask_instagram"], timeout=60, reply_markup=make_keyboard(preference.instagram, [KeyboardButton(data["skip"])]))
        instagram = instagram_ask.text
        preferences.updateByQuery({"user_id": m.from_user.id}, {"name": name})
    except asyncio.TimeoutError:
        return await m.reply_text(data["timeout"])
    except Exception as e:
        return logger.error(f"Error in user input: {e}")

    try:
        phone_ask: Message = await c.ask(m.chat.id, data["ask_phone"], timeout=60, reply_markup=make_keyboard(preference.phone, [KeyboardButton(data["skip"])]))
        phone = phone_ask.text.lstrip("+")
    except asyncio.TimeoutError:
        return await m.reply_text(data["timeout"])
    except Exception as e:
        return logger.error(f"Error in user input: {e}")
    if checker.has_preference(m.from_user.id):
        preferences.updateByQuery(
            {"user_id": m.from_user.id},
            {
                "user_id": m.from_user.id,
                "name": name,
                "lang": fetcher.get_user_lang(m.from_user.id) or "english",
                "gender": gender,
                "age": age,
                "location": new_loc["city"],
                "preffered_gender": preffered_gender,
                "preffered_age_range": preffered_age_range,
                "instagram": instagram if instagram != data["skip"] else None,
                "phone": phone if phone != data["skip"] else None,
            }
        )
    else:
        preferences.add({
            "user_id": m.from_user.id,
            "name": name,
            "lang": fetcher.get_user_lang(m.from_user.id) or "english",
            "gender": gender,
            "age": age,
            "location": new_loc["city"],
            "preffered_gender": preffered_gender,
            "preffered_age_range": preffered_age_range,
            "instagram": instagram if instagram != data["skip"] else None,
            "phone": phone if phone != data["skip"] else None,
            "search_status": 0,
            "current_chat": 0,
            "terms_accepted": 0
        })
    await m.reply_text(data["profile_updated_text"], reply_markup=ReplyKeyboardRemove())

@app.on_message(filters.command("match"))
@app.on_message(filters.command("next"))
async def next_match(c: Client, m: Message):
    current = fetcher.get_preference(m.from_user.id)
    if not current:
        return await m.reply_text("You need to set up your profile first.")
    if current.current_chat:
        return await m.reply_text("You have already an active chat. Send /stop to finish conversation.")
    matcher = Match(m.from_user.id)
    matcher.next_match()
    
@app.on_message(filters.command("stop"))
async def stop_chat(c: Client, m: Message):
    current = fetcher.get_preference(m.from_user.id)
    data = LANGS[fetcher.get_user_lang(m.from_user.id) or "english"]
    if not current:
        return await m.reply_text(data["profile_not_set"])
    if not current.current_chat:
        return await m.reply_text("You have no active chat.")
    preference = fetcher.get_preference(m.from_user.id)
    partner = preference.current_chat
    matcher = Match(m.from_user.id)
    partner = Match(partner)
    await matcher.notify_chat_stopped(app)
    await partner.notify_chat_stopped(app)
    raise StopPropagation

@app.on_message(filters.command("getme"))
async def message(c: Client, m: Message):
    pref = fetcher.get_preference(m.from_user.id)
    if not pref:
        return await m.reply_text("You need to set up your profile first.")
    address = fetcher.get_address(m.from_user.id)
    if not address:
        return await m.reply_text("You need to set up your address by sending /start again.")
    scheme = f"""
**Name:** {pref.name}
**Age:** {pref.age}
**Gender:** {pref.gender}
**Match with:** {pref.preffered_gender}
**Preffered Age:** {pref.preffered_age_range}
**Location:** {address.display_name or address.country}
**Instagram:** {pref.instagram or "none"}
**Phone:** {pref.phone or "none"}
"""
    return await m.reply_text(scheme, quote=True)

@app.on_message()
async def message(c: Client, m: Message):
    current = fetcher.get_preference(m.from_user.id)
    if not current:
        return await m.reply_text("You need to set up your profile first.")
    if not current.current_chat:
        raise StopPropagation
    partner = fetcher.get_preference(current.current_chat)
    await m.copy(partner.user_id)
    raise StopPropagation

async def match_people():
    try:
        users = preferences.getByQuery({"search_status": 1})
        # os.system("cls || clear")
        print(f"Matching {len(users)} users...")
        random.shuffle(users)
        if len(users) < 2: return
        for i in range(0, len(users), 2):
            user, partner = Match(users[i]["user_id"]), Match(users[i+1]["user_id"])
            user.add_partner(int(partner.user_id))
            partner.add_partner(int(user.user_id))
            await user.notify(app)
            await partner.notify(app)
    except Exception as e:
        return logger.error(f"Error in match_people: {e}")
scheduler = AsyncIOScheduler()
scheduler.add_job(match_people, "interval", seconds=2)
app.start()
print("Bot started.")
#scheduler.start()
print("Scheduler started.")
idle()
print("Bot stopped.")
