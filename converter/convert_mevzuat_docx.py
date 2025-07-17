import uuid

from langchain.retrievers.multi_vector import MultiVectorRetriever
from langchain.storage import InMemoryStore
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from unstructured.partition.pdf import partition_pdf

# PDF dosyasını işleyelim
chunks = partition_pdf(
    filename="data/doc/mevzuat.pdf",
    strategy="hi_res",
    infer_table_structure=True,
    extract_image_block_types=["Image"],
    extract_image_block_to_payload=True,
    chunking_strategy="by_title",
    max_characters=10000,
    combine_text_under_n_chars=2000,
    new_after_n_chars=6000,
)

texts = []
tables = []
images = []

for chunk in chunks:
    if "Table" in str(type(chunk)):
        tables.append(chunk)
    elif "CompositeElement" in str(type(chunk)):
        texts.append(chunk)
        for el in chunk.metadata.orig_elements:
            if "Image" in str(type(el)):
                images.append(el)

# Ollama Embeddings
embeddings = OllamaEmbeddings(model="mxbai-embed-large")

# Vectorstore ve Docstore
vectorstore = Chroma(
    collection_name="mevzuat_rag_ollama",
    embedding_function=embeddings,
    persist_directory="./chroma_mevzuat_db",
)

store = InMemoryStore()
id_key = "doc_id"
retriever = MultiVectorRetriever(vectorstore=vectorstore, docstore=store, id_key=id_key)


# Yardımcı fonksiyon
def add_chunks(chunks, kind):
    ids = [str(uuid.uuid4()) for _ in chunks]
    documents = [
        Document(page_content=chunk.text, metadata={id_key: ids[i]})
        for i, chunk in enumerate(chunks)
    ]
    vectorstore.add_documents(documents, ids=ids)
    store.mset(list(zip(ids, chunks)))
    print(f"✅ {kind} vektör olarak eklendi: {len(documents)}")


add_chunks(texts, "Metin")
add_chunks(tables, "Tablo")
add_chunks(images, "Görsel")

print("🎯 Ollama + Chroma ile PDF'ten embedding işlemi tamamlandı.")
