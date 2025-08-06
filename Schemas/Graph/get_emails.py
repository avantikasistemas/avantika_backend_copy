from pydantic import BaseModel

class GetEmails(BaseModel):
    start_date: str
    end_date: str
