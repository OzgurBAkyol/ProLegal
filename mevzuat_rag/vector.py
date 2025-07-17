import os

import pandas as pd

from utils import create_or_update_collections, get_retriever, split_into_chunks

# Sadece koleksiyon oluşturma fonksiyonunu çağır
if __name__ == "__main__":
    create_or_update_collections()
    print("Tüm CSV dosyaları için embedding ve koleksiyonlar güncellendi.")
