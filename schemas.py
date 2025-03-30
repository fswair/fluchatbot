from pydantic import BaseModel
from config.vars import LANGS

class Preference(BaseModel):
    user_id: int
    name: str
    lang: str
    gender: str
    age: int
    location: str | None
    preffered_gender: str
    preffered_age_range: str
    instagram: str | None
    phone: str | None
    search_status: int
    current_chat: int
    terms_accepted: int
    
    @property
    def langdict(self):
        return LANGS[self.lang]


class Address(BaseModel):
    user_id: int
    city: str
    country: str
    country_code: str
    postcode: str
    display_name: str
    latitude: float
    longitude: float
    extra: str