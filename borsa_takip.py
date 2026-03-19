from flask import Flask, render_template_string
import yfinance as yf
import pandas as pd
import ta

app = Flask(__name__)

# --- GÖRSEL ARAYÜZ (HTML/CSS) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Borsa Analiz Pro Dashboard</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <style>
        body { background-color: #f8f9fa; font-family: 'Inter', sans-serif; }
        .card-custom { border-radius: 12px; transition: all 0.3s ease; border: none; }
        .card-custom:hover { transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.1); }
        .rsi-badge { font-size: 0.8rem; padding: 5px 10px; border-radius: 20px; }
        .ticker-name { color: #6c757d; font-size: 0.85rem; }
        .price-text { font-size: 1.25rem; font-weight: 700; color: #2d3436; }
        .market-section { margin-bottom: 40px; }
        .market-title { border-left: 5px solid #0d6efd; padding-left: 15px; margin-bottom: 25px; font-weight: 700; }
        footer {padding-top: 10px !important;}
    </style>
</head>
<body>
    <div class="container mt-5">
        <h2 class="text-center mb-5 fw-bold">Piyasa Analiz Paneli</h2>

        {% for grup_adi, veri in tum_sonuclar.items() %}
            <div class="market-section">
                <h4 class="market-title">{{ grup_adi }}</h4>
                <div class="row g-4">
                    {% for item in veri.fiyatlar %}
                    <div class="col-12 col-md-6 col-lg-4">
                        <div class="card h-100 card-custom shadow-sm bg-white">
                            <div class="card-body">
                                <div class="d-flex justify-content-between align-items-start mb-2">
                                    <div>
                                        <h5 class="fw-bold mb-0">{{ item.ticker }}</h5>
                                        <div class="ticker-name">{{ item.isim }}</div>
                                    </div>
                                    <span class="badge rsi-badge {% if item.rsi < 45 %}bg-success text-white{% else %}bg-light text-dark{% endif %}">
                                        RSI: {{ "%.1f"|format(item.rsi) }}
                                    </span>
                                </div>
                                
                                <div class="mt-3">
                                    <div class="price-text">{{ "%.2f"|format(item.fiyat) }} {{ item.sembol }}</div>
                                </div>

                                <div class="mt-3 border-top pt-2">
                                    {% if item.rsi < 45 %}
                                        <span class="text-success small fw-bold">● Potansiyel Alım Bölgesi</span>
                                    {% else %}
                                        <span class="text-muted small italic">○ Stabil Görünüm</span>
                                    {% endif %}
                                </div>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        {% endfor %}

        <footer class="mt-2 text-center text-muted pb-5">
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-lg-8 border-top pt-4">
                <h6 class="fw-bold text-dark"> Teknik Analiz Bilgi Notu</h6>
                <p class="small mb-2">
                    Bu tabloda hisseler <strong>RSI (Göreceli Güç Endeksi)</strong> değerlerine göre, en düşükten en yükseğe doğru sıralanmıştır. 
                </p>
                <p class="small mb-0 text-start bg-white p-3 rounded shadow-sm">
                    <strong>Potansiyel Alım Bölgesi:</strong> RSI değerinin 45'in altında olması, hissenin teknik olarak "aşırı satım" bölgesine yaklaştığını ve piyasa fiyatının ucuzlamış olabileceğini gösterir. Bu durum, hissede yukarı yönlü bir tepki olasılığının arttığına dair bir sinyal niteliği taşır. RSI 70'in üzerine çıktığında ise hissenin "aşırı alım" (pahalı) bölgesinde olduğu kabul edilir.
                </p>
                <p class="mt-3" style="font-size: 0.75rem;">
                    <em>* Veriler Yahoo Finance üzerinden anlık çekilmektedir. Bu bilgiler kişisel bir analiz aracıdır, yatırım tavsiyesi içermez.</em>
                </p>
            </div>
        </div>
    </div>
</footer>
        <footer class="mt-2 text-center text-muted pb-3">
            <small>Tüm veriler yFinance üzerinden anlık olarak alınmıştır.</small>
        </footer>
    </div>
</body>
</html>
"""

# Yeni Hisse Açıklamaları
HISSE_BILGILERI = {
    # BIST İlk 5
    "TUPRS.IS": "Tüpraş - Petrol Rafinerileri",
    "THYAO.IS": "Türk Hava Yolları - Havacılık",
    "ASELS.IS": "Aselsan - Savunma Sanayii",
    "SISE.IS": "Şişecam - Cam ve Kimyasallar",
    "EREGL.IS": "Erdemir - Demir Çelik",
    
    # S&P 500 İlk 5 (Piyasa Değeri En Yüksekler)
    "MSFT": "Microsoft - Yazılım ve Bulut Devleri",
    "AAPL": "Apple Inc. - Teknoloji ve Donanım",
    "NVDA": "NVIDIA - Yapay Zeka ve Çip Teknolojisi",
    "AMZN": "Amazon - E-Ticaret ve Lojistik",
    "META": "Meta Platforms - Sosyal Medya ve Metaverse",
    
    # Nasdaq İlk 5 (Teknoloji ve İnovasyon)
    "GOOGL": "Alphabet (Google) - Arama Motoru ve Yazılım",
    "TSLA": "Tesla - Elektrikli Araç ve Enerji",
    "AVGO": "Broadcom - Yarı İletken Çözümleri",
    "COST": "Costco Wholesale - Perakende Devleri",
    "ADBE": "Adobe - Yaratıcı Yazılım Çözümleri"
}

def sinyal_tara():
    # Grupları S&P 500, Nasdaq ve BIST olarak 3 sütuna böldük
    gruplar = {
        "BIST İlk 5": ["TUPRS.IS", "THYAO.IS", "ASELS.IS", "SISE.IS", "EREGL.IS"],
        "S&P 500 İlk 5": ["MSFT", "AAPL", "NVDA", "AMZN", "META"],
        "Nasdaq İlk 5": ["GOOGL", "TSLA", "AVGO", "COST", "ADBE"]
    }
    
    # ... (Geri kalan sinyal_tara mantığı aynı kalacak, RSI sıralaması dahil) ...
    
    tum_veriler = {}

    for grup_adi, ticker_listesi in gruplar.items():
        grup_sinyalleri = []
        grup_fiyatlari = []
        
        for ticker in ticker_listesi:
            try:
                df = yf.download(ticker, period="1y", interval="1d", progress=False)
                if df.empty: continue

                son_fiyat = float(df["Close"].iloc[-1].squeeze())
                sembol = "TL" if ".IS" in ticker else "$"
                
                # İndikatörler
                close = df["Close"].astype(float).squeeze()
                df["rsi"] = ta.momentum.RSIIndicator(close=close).rsi()
                current_rsi = float(df["rsi"].iloc[-1])

                # Bilgi ve Fiyat Paketleme
                hisse_data = {
                    "ticker": ticker,
                    "isim": HISSE_BILGILERI.get(ticker, "Borsa Şirketi"),
                    "fiyat": son_fiyat,
                    "sembol": sembol,
                    "rsi": current_rsi
                }
                grup_fiyatlari.append(hisse_data)

                # Alım Koşulu
                if current_rsi < 45:
                    grup_sinyalleri.append(hisse_data)

            except Exception as e:
                print(f"Hata {ticker}: {e}")

        # SIRALAMA MANTIĞI: RSI değerine göre (En düşük RSI en üstte)
        grup_fiyatlari = sorted(grup_fiyatlari, key=lambda x: x['rsi'])
        
        tum_veriler[grup_adi] = {"sinyaller": grup_sinyalleri, "fiyatlar": grup_fiyatlari}

    return tum_veriler
# --- WEB YOLLARI (ROUTES) ---
@app.route('/')
def index():
    sonuclar = sinyal_tara() 
    return render_template_string(HTML_TEMPLATE, tum_sonuclar=sonuclar)

if __name__ == '__main__':
    print("Sunucu başlatılıyor... http://127.0.0.1:5000 adresine gidin.")
    app.run(debug=True, port=5000)
