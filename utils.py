from database import preferences, addresses
from schemas import Preference, Address
from typing import NoReturn, Generic, TypeVar
from geopy import Nominatim

_T = TypeVar("_T")

def get_location(lon: float, lat: float):
    geo = Nominatim(user_agent="user_agent")
    geo = geo.reverse((lat, lon))
    return geo.raw

class checker:
    @staticmethod
    def has_preference(user_id: int):
        return bool(preferences.getBy({"user_id": user_id}))
    @staticmethod
    def has_address(user_id: int):
        return bool(addresses.getBy({"user_id": user_id}))
    @staticmethod
    def terms_accepted(user_id: int):
        result = preferences.getBy({"user_id": user_id})
        if result:
            return bool(result[0].get("terms_accepted"))
        return False

class fetcher:
    @staticmethod
    def get_preference(user_id: int):
        result = preferences.getBy({"user_id": user_id})
        if result:
            return Preference(**result[0])
    @staticmethod
    def get_address(user_id: int):
        result = addresses.getBy({"user_id": user_id})
        if result:
            return Address(**result[0])
    @staticmethod
    def get_user_lang(user_id: int):
        result = preferences.getBy({"user_id": user_id})
        if result:
            return result[0].get("lang")

class Searching(Generic[_T]):
    """Search status of the user"""
    pass

class StopChat(Generic[_T]):
    """Event to stop the chat"""
    pass

class Match:
    def __init__(self, user_id: int):
        self.user_id = user_id
    def next_match(self) -> Searching[NoReturn]:
        print("Next match event")
        preferences.updateByQuery({"user_id": self.user_id}, {"search_status": 1})
    def stop_chat(self) -> StopChat[NoReturn]:
        print("Stop chat event")
        preferences.updateByQuery({"user_id": self.user_id}, {"current_chat": 0, "search_status": 0})
    def add_partner(self, partner_id: int) -> Searching[NoReturn]:
        preferences.updateByQuery({"user_id": self.user_id}, {"current_chat": partner_id, "search_status": 0})
    async def notify(self, client) -> Searching[NoReturn]:
        preference = fetcher.get_preference(self.user_id)
        await client.send_message(self.user_id, preference.langdict["new_match"])
    async def notify_chat_stopped(self, client) -> StopChat[NoReturn]:
        preference = fetcher.get_preference(self.user_id)
        await client.send_message(self.user_id, preference.langdict["chat_stopped"])
        self.stop_chat()
    def __next__(self) -> Searching[NoReturn]:
        self.next_match()
