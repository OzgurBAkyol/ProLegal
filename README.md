# ProLegal: Akıllı Mevzuat ve Parsel Asistanı

## Proje Hakkında
ProLegal, mevzuat ve parsel sorgu işlemlerini bir arada yürütebileceğiniz, RAG tabanlı, modüler ve kullanıcı dostu bir sistemdir. Yapay zeka destekli mevzuat asistanı, parsel/imar sorgulama, poligon analizi ve etiketleme gibi işlevleri tek bir arayüzde sunar. Sistem, hem teknik kullanıcılar hem de son kullanıcılar için kolay ve anlaşılır bir deneyim sunar.

---

## Genel Özellikler ve Yapılanlar
- **Mevzuat Soru-Cevap (RAG Agent):**
  - Mevzuat dosyalarından embedding ile bilgi çekip, OpenRouter LLM ile Türkçe soru-cevap sağlar.
  - Chunk’lama, koleksiyon seçimi ve optimize arama parametreleriyle hızlı ve doğru sonuç üretir.
- **Parsel Sorgu ve Harita:**
  - TKGM API ile parsel sorgulama, harita üzerinde görselleştirme.
  - Taşınmaz pasifse, API yanıtındaki yeni parsele otomatik yönlendirme yapılır ve kullanıcıya bilgi mesajı gösterilir.
  - Koordinatlar sade görünümde, detay isteyen kullanıcı için expander ile gösterilir.
- **İmar Sorgu:**
  - Dilovası Belediyesi imar sorgulama, KML/KMZ dosya işlemleri ve detaylı imar bilgisi sunumu.
- **Poligon Analizi:**
  - Poligonların yapılaşma, yol yakınlığı, eğim gibi özelliklerinin analiz edilmesi ve harita üzerinde gösterimi.
- **Parsel Etiketleme:**
  - 5 sütunlu veri üzerinde 3 sütuna göre filtreleme, satırlara etiket atama, loglama ve Excel’e indirme.
- **Kullanıcı Dostu Arayüz:**
  - Tüm modüller tek bir Streamlit arayüzünde sekmeli olarak sunulur. Koordinatlar ve detaylar expander ile gösterilir.
- **Otomatik Bağımlılık Yönetimi:**
  - requirements.txt dosyası, env’deki tüm paketlerle güncellenebilir.
- **Modüler Kod Yapısı:**
  - Her işlev ayrı fonksiyona/klasöre taşındı, ortak fonksiyonlar için utils klasörü oluşturuldu.

---

## Kurulum
1. **Depoyu Klonlayın:**
   ```bash
   git clone https://github.com/OzgurBAkyol/ProLegal.git
   cd ProLegal
   ```
2. **Sanal Ortam Oluşturun ve Aktif Edin:**
   ```bash
   python3 -m venv legal_env
   source legal_env/bin/activate
   ```
3. **Gerekli Paketleri Yükleyin:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Ekstra Bağımlılıklar (Selenium için):**
   ```bash
   pip install selenium
   # MacOS için:
   brew install chromedriver
   ```

---

## Kullanım
1. **Uygulamayı Başlatın:**
   ```bash
   streamlit run app.py
   ```
2. **Arayüzdeki Modüller ve Kullanım:**
   - **Mevzuat Asistanı:**
     - Türkçe mevzuat sorularınızı yazın, yapay zeka ile cevap alın.
     - Kullanılan veri tabanları ve koleksiyonlar ekranda gösterilir.
   - **Parsel Sorgu ve Harita:**
     - Mahalle, ada, parsel girin, haritada ve tabloda sonucu görün.
     - Taşınmaz pasifse otomatik yeni parsele yönlendirilirsiniz ve bilgi mesajı alırsınız.
     - Koordinatlar sade görünümde, detay isteyen kullanıcı için expander ile gösterilir.
   - **İmar Sorgu:**
     - Ada/parsel ile imar durumu ve KML dosyasını sorgulayın.
     - Sonuçlar tablo ve harita olarak sunulur.
   - **Poligon Analizi:**
     - Poligon, eğim ve OSM verileriyle analiz ve harita görselleştirme.
     - Filtreleme ve detaylı analiz seçenekleri sunar.
   - **Parsel Etiketleme:**
     - Filtreleme, toplu etiketleme ve Excel’e indirme işlemleri.
     - Loglama ve geçmiş işlemler kaydı tutulur.

---

## Modül Detayları ve Çalışma Mantığı
### Mevzuat Soru-Cevap (RAG Agent)
- Soru kutusuna mevzuatla ilgili bir soru yazılır.
- Sistem, embedding ve vektör arama ile ilgili mevzuat parçalarını bulur.
- OpenRouter LLM ile Türkçe cevap oluşturulur.
- Kullanılan koleksiyonlar ve kaynaklar ekranda gösterilir.

### Parsel Sorgu ve Harita
- Mahalle, ada, parsel bilgisi girilir.
- TKGM API’sine sorgu atılır, dönen geometri haritada gösterilir.
- Taşınmaz pasifse, API yanıtındaki yeni parsele otomatik yönlendirme yapılır ve kullanıcıya bilgi mesajı gösterilir.
- Sonuçlar tabloya ve CSV’ye eksiksiz kaydedilir.
- Koordinatlar sade görünümde, detay isteyen kullanıcı için expander ile gösterilir.

### İmar Sorgu
- Ada ve parsel ile belediye API’sine sorgu atılır.
- Dönen imar bilgileri ve KML dosyası harita ve tablo olarak sunulur.
- Sonuçlar CSV’ye kaydedilir.

### Poligon Analizi
- Poligonların centroid noktası üzerinden eğim (slope) verisi alınır.
- OSM’den yol ve yapı geometrileri çekilir.
- Tüm analizler harita ve tabloya yansıtılır.
- Filtreleme ve detaylı analiz seçenekleri sunar.

### Parsel Etiketleme
- Excel dosyasındaki parseller filtrelenir.
- Seçilen satırlara etiket atanır ve sonuçlar kaydedilip indirilebilir.
- Loglama ve geçmiş işlemler kaydı tutulur.

---

## Veri ve Dosya Yapısı
- **data/**: Tüm veri dosyaları (CSV, poligon, slope, OSM, KML, vb.)
- **converter/**: Dönüştürücü ve yardımcı scriptler
- **utils/**: Ortak fonksiyonlar ve yardımcı modüller
- **mevzuat_rag/**: Mevzuat RAG ve LLM ile ilgili modüller
- **visual_map/**: Harita görselleri ve HTML çıktıları
- **kml_parseller/**: KML/KMZ dosyaları

---

## Sıkça Sorulan Sorular
- **Taşınmaz pasifse ne olur?**
  - Sistem otomatik olarak yeni (aktif) parsele yönlendirir ve kullanıcıya bilgi mesajı gösterir.
- **Tabloda neden boş alanlar var?**
  - Tüm property anahtarları otomatik eşleştirilir ve None değerler boş string olarak yazılır. Tabloda ana bilgiler her zaman eksiksiz görünür.
- **Koordinatlar neden gizli?**
  - Arayüzde sade görünüm için koordinatlar expander ile gösterilir, detay isteyen kullanıcı açıp bakabilir.

---

## Katkı ve Geliştirme
- Kod modüler ve okunabilir şekilde tasarlanmıştır.
- Yeni modül eklemek için utils veya ilgili klasöre fonksiyon ekleyebilirsiniz.
- Pull request ve issue açarak katkıda bulunabilirsiniz.

---

## Lisans
MIT

---

## İletişim
Her türlü soru, öneri ve katkı için:
[OzgurBAkyol/ProLegal GitHub](https://github.com/OzgurBAkyol/ProLegal)
