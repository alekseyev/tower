from pydantic import BaseModel


class State(BaseModel):
    user_id: str | None = None
