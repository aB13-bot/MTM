import chromadb
from sentence_transformers import SentenceTransformer
import os
from pathlib import Path

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="mother_knowledge")

model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

docs_dir = Path("./data")
documents = []
metadatas = []
ids = []

for file_path in docs_dir.glob("*.md"):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        chunks = content.split("\n\n")
        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) < 20:
                continue
            documents.append(chunk)
            metadatas.append({"source": file_path.name})
            ids.append(f"{file_path.stem}_{i}")

if documents:
    embeddings = model.encode(documents).tolist()
    collection.add(
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    print(f"成功存入 {len(documents)} 个知识片段")
else:
    print("没有找到文档")