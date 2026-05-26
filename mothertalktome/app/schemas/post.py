from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List

class PostCreate(BaseModel):
    title: str
    content: str

class PostResponse(BaseModel):
    id: UUID
    user_id: str
    title: str
    content: str
    created_at: datetime
    comments: List["CommentResponse"] = []
    
    class Config:
        from_attributes = True

class CommentCreate(BaseModel):
    content: str
    parent_id: Optional[UUID] = None

class CommentResponse(BaseModel):
    id: UUID
    post_id: UUID
    user_id: str
    content: str
    is_ai: bool
    created_at: datetime
    
    
    class Config:
        from_attributes = True

PostResponse.model_rebuild()
CommentResponse.model_rebuild()