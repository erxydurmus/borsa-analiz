##  Canlı Uygulama / Live Demo
Uygulamayı buradan inceleyebilirsiniz: [Borsa Analiz Paneli](https://borsa-analiz-9f8m.onrender.com)

*(Not: Ücretsiz sunucu kullanıldığı için ilk açılış 30-50 saniye sürebilir.)*

# Borsa Teknik Analiz ve Sinyal Takip Sistemi

Bu proje, Python tabanlı bir mikro web servisidir. Finansal piyasalardaki teknik verileri analiz ederek belirli stratejilere göre alım sinyalleri üretir ve kullanıcıya iletir.

## Özet
**Yahoo Finance API**'sini kullanarak canlı olarak borsa verilerini çeker, **Pandas** ve **Technical Analysis (ta)** kütüphaneleriyle verileri işleyip teknik stratejilere göre filtreleme yapar. Sonuçları **Flask** ve **Bootstrap** kullanarak kullanıcıya modern bir web arayüzü üzerinden sunar.

## Kullanılan Teknolojiler
* **Dil:** Python
* **Web Framework:** Flask
* **Veri Analizi:** Pandas, NumPy
* **Finans:** yfinance, ta-lib (ta)
* **Frontend:** HTML5, Bootstrap 5

## Teknik Strateji (Alım Koşulları)
Uygulama, bir hisse için şu koşullar aynı anda sağlandığında sinyal üretir:
1. **RSI < 45:** Aşırı satım bölgesine yakınlık.
2. **MACD > Signal:** Pozitif yönlü trend kesişimi.
3. **Fiyat > EMA50:** Orta vadeli yükseliş trendi.
4. **EMA50 > EMA200:** Uzun vadeli pozitif görünüm (Golden Cross hazırlığı).
5. **Hacim > Ortalama Hacim:** İşleme olan ilginin artışı.