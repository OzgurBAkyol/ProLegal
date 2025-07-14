# NOT: Bu script embedding işlemi yapmaz, sadece mevcut chroma_db altındaki tüm koleksiyonlardan veri sorgular.
# Eğer yeni belge eklediyseniz, önce ilgili embedding scriptini (vector.py veya embed_all_pdfs.py) çalıştırmalısınız.

from langchain_core.prompts import ChatPromptTemplate
from openrouter_llm import OpenRouterLLM
from vector import get_retriever
import os

DB_DIR = "./chroma_db"

def get_all_collections(db_dir):
    collections = set()
    for entry in os.listdir(db_dir):
        path = os.path.join(db_dir, entry)
        # Klasör ise koleksiyon olarak ekle
        if os.path.isdir(path) and not entry.startswith('.'):
            collections.add(entry)
        # .sqlite3 dosyası ise, dosya adını koleksiyon olarak ekle (ana veritabanı hariç)
        elif entry.endswith('.sqlite3') and entry != "chroma.sqlite3":
            collections.add(entry.replace('.sqlite3', ''))
    return list(collections)

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

while True:
    print("\n\n-------------------------------")
    question = input("Sorunuzu yazın (q ile çık): ")
    if question == "q":
        break
    reviews, used_collections = merged_retrieve(question)
    result = chain.invoke({"reviews": reviews, "question": question})
    if used_collections:
        result += "\n\n---\nBu cevabın oluşturulmasında kullanılan veritabanları: " + ", ".join(used_collections)
    else:
        result += "\n\n---\nBu cevabın oluşturulmasında hiçbir veritabanı kullanılmadı."
    print(result) 