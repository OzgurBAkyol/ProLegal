# NOT: Bu script embedding işlemi yapmaz, sadece mevcut chroma_db altındaki tüm koleksiyonlardan veri sorgular.
# Eğer yeni belge eklediyseniz, önce ilgili embedding scriptini (vector.py veya embed_all_pdfs.py) çalıştırmalısınız.

import os

from langchain_core.prompts import ChatPromptTemplate

from utils import OpenRouterLLM, get_all_collections, get_retriever

DB_DIR = "./chroma_db"

COLLECTIONS = get_all_collections(DB_DIR)
retrievers = [get_retriever(collection) for collection in COLLECTIONS]


def merged_retrieve(question, k=20):
    results = []
    used_collections = []
    for idx, retriever in enumerate(retrievers):
        collection_name = COLLECTIONS[idx]
        try:
            docs = retriever.invoke(question)
            if docs:
                used_collections.append(collection_name)
            if isinstance(docs, list):
                results.extend(docs)
            else:
                results.append(docs)
        except Exception:
            continue
    return results[:k], used_collections


model = OpenRouterLLM(model="deepseek/deepseek-r1-0528:free")

prompt = ChatPromptTemplate.from_template(
    """
You are an expert assistant specialized in Turkish land registry, parcel, and property data queries. You help users by interpreting legal, technical, and administrative information, and you are familiar with APIs, data formats, and official documentation. Always answer in Turkish, even if the prompt is in English. Use the provided context and data to give clear, concise, and accurate answers to user questions about land, property, or related legal/technical issues. If the user asks about a specific parcel, property, or API response, analyze the data and explain it in Turkish. If you don't know the answer, say you don't know in Turkish.

Context:
{reviews}

User question (in Turkish): {question}

Your answer (in Turkish):
"""
)

chain = prompt | model

# FastAPI ve API ile ilgili tüm kodları kaldırıyorum
# (app = FastAPI(), CORS ayarları, AskRequest, ask_endpoint, ve ilgili importlar)

# from api_main2 import FastAPI, Request  # Zaten kaldırıldı
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# import uvicorn

# FastAPI uygulaması oluştur
# app = FastAPI()

# CORS ayarları (gerekirse)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# class AskRequest(BaseModel):
#     question: str

# @app.post("/ask")
# async def ask_endpoint(req: AskRequest):
#     question = req.question
#     reviews, used_collections = merged_retrieve(question)
#     result = chain.invoke({"reviews": reviews, "question": question})
#     if used_collections:
#         result += "\n\n---\nBu cevabın oluşturulmasında kullanılan veritabanları: " + ", ".join(used_collections)
#     else:
#         result += "\n\n---\nBu cevabın oluşturulmasında hiçbir veritabanı kullanılmadı."
#     return {"answer": result, "used_collections": used_collections}


def test_embedding_arama(sorgu, k=10):
    print(f"\n[DEBUG] '{sorgu}' için ilk {k} chunk arama sonuçları:")
    results, used_collections = merged_retrieve(sorgu, k=k)
    for idx, doc in enumerate(results):
        print(f"\n--- Sonuç {idx+1} ---\n{doc}")
    print(f"\nKullanılan koleksiyonlar: {used_collections}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "api":
        # uvicorn.run("agent:app", host="0.0.0.0", port=8001, reload=True) # FastAPI kaldırıldı
        pass  # FastAPI kaldırıldı
    elif len(sys.argv) > 2 and sys.argv[1] == "test_embed":
        test_embedding_arama(sys.argv[2], k=20)
    else:
        while True:
            print("\n\n-------------------------------")
            question = input("Sorunuzu yazın (q ile çık): ")
            if question == "q":
                break
            reviews, used_collections = merged_retrieve(question)
            result = chain.invoke({"reviews": reviews, "question": question})
            if used_collections:
                result += (
                    "\n\n---\nBu cevabın oluşturulmasında kullanılan veritabanları: "
                    + ", ".join(used_collections)
                )
            else:
                result += "\n\n---\nBu cevabın oluşturulmasında hiçbir veritabanı kullanılmadı."
            print(result)
