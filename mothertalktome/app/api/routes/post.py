from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import List

from app.auth.dependencies import get_current_user
from app.core import database_session
from app.auth.models import User
from app.schemas.post import PostCreate, PostResponse, CommentCreate, CommentResponse
from app.models.post import Post, Comment
from app.services.llm_service import generate_mother_reply
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()

@router.post("/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_in: PostCreate,
    current_user: User = Depends(get_current_user),  
    session: AsyncSession = Depends(database_session.new_async_session)
):
    """创建新帖子"""
    new_post = Post(
        title=post_in.title,
        content=post_in.content,
        user_id=current_user.user_id,
    )

    session.add(new_post)
    await session.commit()
    await session.refresh(new_post)

    return PostResponse(
        id=new_post.id,
        user_id=new_post.user_id,
        title=new_post.title,
        content=new_post.content,
        created_at=new_post.created_at,
        comments=[] 
    )

@router.get("/posts", response_model=List[PostResponse])
async def get_posts(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(database_session.new_async_session)
):
    """获取帖子列表（分页）"""
    skip = (page - 1) * size

    result = await session.execute(
        select(Post)
        .order_by(desc(Post.created_at))
        .offset(skip)
        .limit(size)
        .options(selectinload(Post.comments))
    )

    posts = result.scalars().all()
    return posts        
    

@router.get("/posts/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: UUID,
    session: AsyncSession = Depends(database_session.new_async_session)
):
    result = await session.execute(
        select(Post)
        .where(Post.id == post_id)
        .options(selectinload(Post.comments))  
    )
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="帖子不存在"

        )
    return post
    

@router.post("/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    post_id: UUID,
    comment_in: CommentCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(database_session.new_async_session),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    post = await session.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
  
    if comment_in.parent_id:
        parent_comment = await session.get(Comment, comment_in.parent_id)
        if not parent_comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="回复的评论不存在"
            )
        

    new_comment = Comment(
        content=comment_in.content,
        post_id=post_id,
        user_id=current_user.user_id,
        parent_id=comment_in.parent_id,
        is_ai=False
    )
    
    session.add(new_comment)
    await session.commit()
    await session.refresh(new_comment)

    if "@Mother" in comment_in.content :
        background_tasks.add_task(
            process_ai_reply,
            post_id,
            comment_in.content,
            post.content,
            current_user.user_id
        )

    return new_comment

async def process_ai_reply(
    post_id: UUID,
    user_comment: str,
    post_content: str,
    user_id: str,
):
    
    from app.core import database_session
    from app.models.post import Comment
    from app.core.config import get_settings
    from app.services.llm_service import generate_mother_reply, extract_user_traits
    from app.auth.models import User

    settings = get_settings()
    
    try:

        async for session in database_session.new_async_session():
            user = await session.get(User, user_id)
            current_memory = user.bio_memory if user and user.bio_memory else ""
        
        ai_reply = await generate_mother_reply(
            user_comment=user_comment, 
            post_content=post_content,
            user_memory=current_memory 
        )
        
        
        ai_comment = Comment(
            content=ai_reply,
            post_id=post_id,
            user_id=settings.ai_mother_user_id,
            parent_id=None,
            is_ai=True
        )
        session.add(ai_comment)
        
        new_memory = await extract_user_traits(user_comment, current_memory)
        
        if user:
            user.bio_memory = new_memory

            await session.commit()
            print(f"AI已回复帖子 {post_id}，并更新了记忆")

    except Exception as e:
        print(f"AI回复失败: {e}")
