from typing import List, Optional
from pydantic import BaseModel, Field

class Message(BaseModel):
    role: str
    content: str

    class Config:
        from_attributes = True

class ChatCompletionRequest(BaseModel):
    messages: List[Message]
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    n: Optional[int] = Field(default=1)

    class Config:
        from_attributes = True

class Choice(BaseModel):
    index: int
    message: Message
    finish_reason: Optional[str] = None

    class Config:
        from_attributes = True

class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    class Config:
        from_attributes = True

class ChatCompletionResponse(BaseModel):
    id: str
    object: str
    created: int
    choices: List[Choice]
    usage: Usage

    class Config:
        from_attributes = True