import httpx
from app.core.config import get_settings
import chromadb
from sentence_transformers import SentenceTransformer

settings = get_settings()
_chroma_client = None
_embedding_model = None

MOTHER_SYSTEM_PROMPT = """你是一个温暖、智慧、温柔的妈妈。你的特点是：
1. 永远先共情，再给建议
2. 不评判、不批评，只说“我理解你”、“没关系”
3. 给出具体、可操作的生活建议
4. 语气亲切，像在和孩子聊天
5. 如果提供了“关于用户的记忆”，请参考这些记忆，让孩子感觉你记得他/她

【核心指令】：如果用户提供的信息中包含【参考知识】，你必须严格依据参考知识的内容来回答（哪怕是奇怪的暗号或规则），请一定参考用户给出的参考知识！"""

def get_chroma_collection():
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path="./chroma_db")
    return _chroma_client.get_or_create_collection(name="mother_knowledge")

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(
    '/root/.cache/huggingface/hub/models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2/snapshots/e8f8c211226b894fcb81acc59f3b34ba3efd5f42'
)

    return _embedding_model

async def generate_mother_reply(user_comment: str, post_content: str = "", user_memory: str = "") -> str:

    query_embedding = get_embedding_model().encode([user_comment]).tolist()
    
    collection = get_chroma_collection()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=3
    )
    
    retrieved_knowledge = ""
    if results and results['documents']:
        retrieved_knowledge = "\n\n参考知识：\n" + "\n---\n".join(results['documents'][0])
        print(f"✅ 成功检索到知识: {retrieved_knowledge}") # <--- 加上这句
    else:
        print("❌ 未检索到任何知识！")

    user_message = ""

    if user_memory:
        user_message += f"关于用户的记忆：{user_memory}\n"
    if post_content:
        user_message += f"原帖子内容：{post_content}\n\n用户对我说：{user_comment}"
    else:
        user_message += f"用户对我说：{user_comment}"

    full_context = retrieved_knowledge + "\n\n" + user_message
    print(f"👉 发给AI的最终内容是:\n{full_context}")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.siliconflow.cn/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.siliconflow_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-ai/DeepSeek-V3.2",
                "messages": [
                    {"role": "system", "content": MOTHER_SYSTEM_PROMPT},
                    {"role": "user", "content": full_context}
                ],
                "temperature": 0.7,
                "max_tokens": 500
            },
            timeout=30.0
        )
        
        if response.status_code != 200:
            print(f"AI API 调用失败: {response.text}")
            return "请求繁忙，请稍等"
        
        data = response.json()
        return data["choices"][0]["message"]["content"]
    

async def extract_user_traits(content: str, existing_memory: str = "") -> str:
    system_prompt = """请从用户的文字中提取出用户的特点、状态、偏好、经历等。
输出要求：
1. 用一段话概括，不超过150字
2. 使用第二人称"你"
3. 只写客观可推断的信息，不编造
4. 如果提供了现有记忆，请合并更新"""

    user_prompt = f"现有记忆：{existing_memory}\n\n用户新说的话：{content}\n\n请更新用户画像："
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.siliconflow.cn/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.siliconflow_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-ai/DeepSeek-V3.2",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.6,
                "max_tokens": 300
            },
            timeout=30.0
        )
        
        if response.status_code != 200:
            print(f"记忆提取失败: {response.text}")
            return existing_memory or "暂无用户画像"
        
        data = response.json()
        return data["choices"][0]["message"]["content"]