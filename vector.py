import os
import pandas as pd
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

CSV_DIR = "data/csv"
DB_DIR = "./chroma_db"
EMBED_MODEL = "mxbai-embed-large"

os.makedirs(DB_DIR, exist_ok=True)

embeddings = OllamaEmbeddings(model=EMBED_MODEL)

for csv_file in os.listdir(CSV_DIR):
    if not csv_file.endswith(".csv"):
        continue
    csv_path = os.path.join(CSV_DIR, csv_file)
    df = pd.read_csv(csv_path)
    collection_name = os.path.splitext(csv_file)[0]
    db_location = os.path.join(DB_DIR, collection_name)
    add_documents = not os.path.exists(db_location)

    if add_documents:
        documents = []
        ids = []
        for i, row in df.iterrows():
            # İçerik kolonunu bul
            content = ""
            if "İçerik" in row:
                content = str(row["İçerik"])
            else:
                # Fallback: ilk metin kolonunu bul
                for col in df.columns:
                    if df[col].dtype == object:
                        content = str(row[col])
                        break
            document = Document(
                page_content=content,
                metadata={col: str(row[col]) for col in df.columns if col != "İçerik"},
                id=f"{collection_name}_{i}"
            )
            ids.append(f"{collection_name}_{i}")
            documents.append(document)

    vector_store = Chroma(
        collection_name=collection_name,
        persist_directory=db_location,
        embedding_function=embeddings
    )

    if add_documents:
        vector_store.add_documents(documents=documents, ids=ids)

    print(f"✅ {csv_file} için embedding ve vektör veritabanı oluşturuldu.")

def get_retriever(collection_name, k=5):
    db_location = os.path.join(DB_DIR, collection_name)
    vector_store = Chroma(
        collection_name=collection_name,
        persist_directory=db_location,
        embedding_function=embeddings
    )
    return vector_store.as_retriever(search_kwargs={"k": k}) 