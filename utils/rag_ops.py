import os
import re

import pandas as pd
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings

CSV_DIR = "data/csv"
DB_DIR = "./chroma_db"
EMBED_MODEL = "mxbai-embed-large"

os.makedirs(DB_DIR, exist_ok=True)
embeddings = OllamaEmbeddings(model=EMBED_MODEL)


def split_into_chunks(text):
    chunks = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [chunk.strip() for chunk in chunks if chunk.strip()]


def create_or_update_collections():
    for csv_file in os.listdir(CSV_DIR):
        if not csv_file.endswith(".csv"):
            continue
        csv_path = os.path.join(CSV_DIR, csv_file)
        collection_name = os.path.splitext(csv_file)[0]
        db_location = os.path.join(DB_DIR, collection_name)
        add_documents = not os.path.exists(db_location)
        if add_documents:
            df = pd.read_csv(csv_path)
            documents = []
            ids = []
            for i, row in df.iterrows():
                content = (
                    str(row["İçerik"]) if "İçerik" in row else str(row[df.columns[0]])
                )
                for j, chunk in enumerate(split_into_chunks(content)):
                    document = Document(
                        page_content=chunk,
                        metadata={
                            col: str(row[col]) for col in df.columns if col != "İçerik"
                        },
                        id=f"{collection_name}_{i}_{j}",
                    )
                    ids.append(f"{collection_name}_{i}_{j}")
                    documents.append(document)
            vector_store = Chroma(
                collection_name=collection_name,
                persist_directory=db_location,
                embedding_function=embeddings,
            )
            vector_store.add_documents(documents=documents, ids=ids)


def get_retriever(collection_name, k=20):
    db_location = os.path.join(DB_DIR, collection_name)
    vector_store = Chroma(
        collection_name=collection_name,
        persist_directory=db_location,
        embedding_function=embeddings,
    )
    return vector_store.as_retriever(search_kwargs={"k": k})


def get_all_collections(db_dir=DB_DIR):
    collections = set()
    for entry in os.listdir(db_dir):
        path = os.path.join(db_dir, entry)
        if os.path.isdir(path) and not entry.startswith("."):
            collections.add(entry)
        elif entry.endswith(".sqlite3") and entry != "chroma.sqlite3":
            collections.add(entry.replace(".sqlite3", ""))
    return list(collections)
