import os
import uuid
from unstructured.partition.pdf import partition_pdf
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain.storage import InMemoryStore
from langchain.retrievers.multi_vector import MultiVectorRetriever

PDF_DIR = "data/pdf"
DB_DIR = "./chroma_db"
EMBED_MODEL = "mxbai-embed-large"

os.makedirs(DB_DIR, exist_ok=True)

embeddings = OllamaEmbeddings(model=EMBED_MODEL)

for pdf_file in os.listdir(PDF_DIR):
    if not pdf_file.lower().endswith(".pdf"):
        continue
    pdf_path = os.path.join(PDF_DIR, pdf_file)
    collection_name = os.path.splitext(pdf_file)[0]
    db_location = os.path.join(DB_DIR, collection_name)
    print(f"\n--- {pdf_file} işleniyor ---")

    chunks = partition_pdf(
        filename=pdf_path,
        strategy="hi_res",
        infer_table_structure=True,
        extract_image_block_types=["Image"],
        extract_image_block_to_payload=True,
        chunking_strategy="by_title",
        max_characters=10000,
        combine_text_under_n_chars=2000,
        new_after_n_chars=6000,
    )

    texts, tables, images = [], [], []
    for chunk in chunks:
        if "Table" in str(type(chunk)):
            tables.append(chunk)
        elif "CompositeElement" in str(type(chunk)):
            texts.append(chunk)
            for el in getattr(chunk.metadata, "orig_elements", []):
                if "Image" in str(type(el)):
                    images.append(el)

    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=db_location
    )
    store = InMemoryStore()
    id_key = "doc_id"
    retriever = MultiVectorRetriever(vectorstore=vectorstore, docstore=store, id_key=id_key)

    def add_chunks(chunks, kind):
        ids = [str(uuid.uuid4()) for _ in chunks]
        documents = [Document(page_content=getattr(chunk, "text", str(chunk)), metadata={id_key: ids[i]}) for i, chunk in enumerate(chunks)]
        if documents:
            vectorstore.add_documents(documents, ids=ids)
            store.mset(list(zip(ids, chunks)))
            print(f"✅ {kind} vektör olarak eklendi: {len(documents)}")

    add_chunks(texts, "Metin")
    add_chunks(tables, "Tablo")
    add_chunks(images, "Görsel")
    print(f"🎯 {pdf_file} için embedding işlemi tamamlandı.") 