from pydantic import BaseModel, validator, HttpUrl, UUID4
from typing import Optional, List

class UserSchema(BaseModel):
    username: str
    password: str

    @validator("username")
    def validator_username(cls, username: str):
        if (len(username) < 8):
            raise ValueError("The username must contain more than 8 characters.")
        else:
            return username
    
    @validator("password")
    def validator_password(cls, password: str):
        if (len(password) < 8):
            raise ValueError("The password must contain more than 8 characters.")
        else:
            return password

class CreateOfferSchema(BaseModel):
    title:           str
    text:            str
    links:           Optional[List[HttpUrl]] = []
    category:        str
    expire_in_years: Optional[int]
    
    @validator("category")
    def validator_category(cls, category: str):
        return category

    @validator("title")
    def validator_title(cls, title: str):
        if (len(title) > 64):
            raise ValueError("The maximum length is 64 characters.")
        elif (len(title) < 8):
            raise ValueError("The minimum length is 8 characters.")
        else:
            return title
    
    @validator("text")
    def validator_text(cls, text: str):
        if (len(text) > 1024):
            raise ValueError("The maximum length is 1024 characters.")
        elif (len(text) < 64):
            raise ValueError("The minimum length is 64 characters.")
        else:
            return text

class ReserveOfferSchema(BaseModel):
    offer_id: UUID4
    day:      int
    value:    float

    @validator("day")
    def validator_day(cls, day: int):
        if (day > 365):
            raise ValueError("Day must be less than 365.")
        elif (day < 1):
            raise ValueError("Day must be greater than 1.")
        else:
            return day
    
    @validator("value")
    def validator_value(cls, value: float):
        if (value < 1):
            raise ValueError("Value must be greater than 1.")
        else:
            return value
    
class ProposalDaySchema(BaseModel):
    offer_id: UUID4
    day:      int

class ProposalVoteSchema(BaseModel):
    proposal_id: UUID4