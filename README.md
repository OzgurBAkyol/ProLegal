# ProLegal: Akıllı Mevzuat ve Parsel Asistanı

## Genel Bakış
ProLegal, mevzuat ve parsel sorgu işlemlerini bir arada yürütebileceğiniz, RAG tabanlı ve modüler bir sistemdir. Mevzuat embedding, ChromaDB ile vektör arama, OpenRouter LLM ile Türkçe soru-cevap, TKGM ve belediye API'leriyle parsel/imar sorgu, poligon analiz ve etiketleme gibi işlevleri tek bir modern arayüzde sunar.

---

## Özellikler
- **Mevzuat RAG & Embedding:**
  - Mevzuat dosyalarını embed edip ChromaDB’de saklama
  - Koleksiyonlardan vektör arama ve OpenRouter LLM ile Türkçe cevap
  - Kullanılan koleksiyonların otomatik raporlanması
- **Parsel & İmar Sorgu:**
  - TKGM API ile parsel sorgulama, harita görselleştirme, CSV kaydı
  - Dilovası Belediyesi imar sorgu, KML/KMZ dosya desteği, detaylı hata yönetimi
- **Poligon Analizi:**
  - Poligonların yapılaşma, yol yakınlığı, eğim gibi özelliklerinin analizi
  - OSM ve raster verilerle harita üzerinde görselleştirme
- **Etiketleme & Filtreleme:**
  - Parsel verisi üzerinde çoklu filtreleme ve toplu etiketleme
  - Loglama ve Excel’e indirme
- **Modern Streamlit Arayüzü:**
  - Tüm işlevler sekmeli ve kullanıcı dostu bir arayüzde
  - Yardım, açıklama ve hata mesajları ile profesyonel deneyim
- **Modüler Kod Yapısı:**
  - Tüm yardımcı fonksiyonlar `utils/` klasöründe
  - Her işlev ayrı modül/fonksiyon olarak düzenlendi
  - Kod tekrarları ve dağınıklık ortadan kaldırıldı

---

## Klasör Yapısı
```
ProLegal/
  app.py                  # Ana Streamlit arayüzü (sekme bazlı)
  utils/                  # Ortak yardımcı fonksiyonlar (dosya, geo, etiket, rag, llm, ui)
  mevzuat_rag/            # Mevzuat embedding, RAG ve LLM entegrasyonu
  tkgm/                   # TKGM parsel sorgu API ve yardımcıları
  imar_sorgu/             # Belediye imar sorgu API ve yardımcıları
  poli_analiz/            # Poligon analiz modülü
  etiket_filtre/          # Parsel etiketleme ve filtreleme modülü
  converter/              # Mevzuat ve PDF embedding scriptleri
  data/                   # Tüm veri, csv, json, kml, osm, slope, vb.
  requirements.txt        # Gerekli Python paketleri
  README.md               # Proje dökümantasyonu
```

---

## Kurulum
1. Python 3.10+ ve pip yüklü olmalı.
2. Gerekli paketleri yükleyin:
   ```bash
   pip install -r requirements.txt
   ```
3. `.env` dosyanıza OpenRouter API anahtarınızı ekleyin:
   ```env
   OPENROUTER_API_KEY=xxx
   ```
4. Gerekli veri dosyalarını `data/` klasörüne yerleştirin.

---

## Kullanım
Ana arayüzü başlatmak için:
```bash
streamlit run app.py
```

Her sekmede açıklama, yardım ve örnekler yer almaktadır. Hatalar kullanıcı dostu şekilde gösterilir.

---

## Geliştirici Notları
- Tüm yardımcı fonksiyonlar ve tekrar eden kodlar `utils/` klasörüne taşınmıştır.
- Kodun her bölümü açıklamalı ve fonksiyonel olarak ayrılmıştır.
- Yeni işlev eklemek için ilgili modüle fonksiyon ekleyip, arayüze entegre edebilirsiniz.

---

## Lisans
MIT
