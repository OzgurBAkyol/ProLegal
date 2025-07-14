from langchain_core.prompts import ChatPromptTemplate
from openrouter_llm import OpenRouterLLM
from vector import get_retriever
import os

# Tüm koleksiyonları otomatik olarak birleştir
DB_DIR = "./chroma_db"
COLLECTIONS = [name for name in os.listdir(DB_DIR) if os.path.isdir(os.path.join(DB_DIR, name)) and not name.startswith('.')]

retrievers = [get_retriever(collection) for collection in COLLECTIONS]

def merged_retrieve(question, k=5):
    results = []
    for retriever in retrievers:
        try:
            docs = retriever.invoke(question)
            if isinstance(docs, list):
                results.extend(docs)
            else:
                results.append(docs)
        except Exception:
            continue
    # En alakalı ilk k sonucu döndür
    return results[:k]

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
    reviews = merged_retrieve(question)
    result = chain.invoke({"reviews": reviews, "question": question})
    print(result) 