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
    <title>Borsa Analiz Paneli</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <style>
        body { background-color: #f4f7f6; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .card { border: none; border-radius: 15px; }
        .status-card { transition: transform 0.2s; }
        .status-card:hover { transform: translateY(-5px); }
        .table-dark { background-color: #2c3e50; }
    </style>
</head>
<body>
    <div class="container mt-5">
        <h2 class="mb-4 text-center fw-bold text-dark">📊 Borsa Teknik Analiz Takip</h2>
        
        <div class="card shadow-lg mb-5">
            <div class="card-body p-4">
                {% if sinyaller %}
                    <h5 class="text-success mb-3">🟢 Aktif Alım Sinyalleri</h5>
                    <div class="table-responsive">
                        <table class="table table-hover align-middle">
                            <thead class="table-dark">
                                <tr>
                                    <th>Hisse</th>
                                    <th>Fiyat</th>
                                    <th>RSI</th>
                                    <th>MACD</th>
                                    <th>Durum</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for row in sinyaller %}
                                <tr>
                                    <td><strong>{{ row['ticker'] }}</strong></td>
                                    <td>{{ "%.2f"|format(row['Close']) }} TL</td>
                                    <td><span class="badge bg-primary">{{ "%.2f"|format(row['rsi']) }}</span></td>
                                    <td>{{ "%.4f"|format(row['macd']) }}</td>
                                    <td><span class="badge bg-success">AL KOŞULU</span></td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                {% else %}
                    <div class="alert alert-warning text-center border-0 shadow-sm">
                        <strong>Bilgi:</strong> Şu an kriterlere uygun teknik bir alım sinyali bulunmuyor.
                    </div>
                {% endif %}
            </div>
        </div>

        <div class="mt-4">
            <h4 class="text-center mb-4 text-secondary">🔍 İzleme Listesi Güncel Fiyatlar</h4>
            <div class="row g-3 justify-content-center">
                {% for item in fiyatlar %}
                <div class="col-6 col-md-2">
                    <div class="card h-100 shadow-sm text-center bg-white py-3 status-card border-top border-primary border-4">
                        <div class="small text-muted mb-1 fw-bold">{{ item.ticker }}</div>
                        <div class="h5 mb-0 text-dark fw-bold">{{ "%.2f"|format(item.fiyat) }} TL</div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>

        <footer class="text-muted mt-5 text-center pb-5">
            <small>Veriler Yahoo Finance üzerinden anlık çekilmektedir. Yatırım tavsiyesi değildir.</small>
        </footer>
    </div>
</body>
</html>
"""

# --- ANALİZ MOTORU ---
def sinyal_tara():
    tickers = ["TUPRS.IS", "SISE.IS", "KRDMD.IS", "ASELS.IS", "THYAO.IS", "EREGL.IS"]
    tum_sinyaller = []
    izleme_listesi = []

    for ticker in tickers:
        try:
            # 1. Veri İndirme
            df = yf.download(ticker, period="1y", interval="1d", progress=False)
            if df.empty:
                continue

            # 2. Temel Fiyat Bilgisi (Squeeze ile tekil değere çekiyoruz)
            son_fiyat = float(df["Close"].iloc[-1].squeeze())
            izleme_listesi.append({"ticker": ticker, "fiyat": son_fiyat})

            # 3. İndikatör Hesaplamaları
            close = df["Close"].astype(float).squeeze()
            volume = df["Volume"].astype(float).squeeze()

            # RSI
            df["rsi"] = ta.momentum.RSIIndicator(close=close, window=14).rsi()
            
            # MACD
            macd = ta.trend.MACD(close=close)
            df["macd"] = macd.macd()
            df["macd_signal"] = macd.macd_signal()
            
            # Ortalamalar
            df["ema50"] = ta.trend.EMAIndicator(close=close, window=50).ema_indicator()
            df["ema200"] = ta.trend.EMAIndicator(close=close, window=200).ema_indicator()
            df["volume_ma20"] = volume.rolling(window=20).mean()

            # 4. Alım Stratejisi
            buy_signal_series = (
                (df["rsi"] < 48) & 
                (df["macd"] > df["macd_signal"]) &
                (close > df["ema50"]) &
                (df["ema50"] > df["ema200"]) &
                (volume > df["volume_ma20"])
            )

            df["buy_signal"] = buy_signal_series
            sinyalli_gunler = df[df["buy_signal"]].copy()

            if not sinyalli_gunler.empty:
                sinyalli_gunler["ticker"] = ticker
                # En son sinyal veren günü al
                tum_sinyaller.append(sinyalli_gunler.tail(1).reset_index())
        
        except Exception as e:
            print(f"Hata oluştu ({ticker}): {e}")
            continue

    # Verileri Flask'a gönderilecek şekilde paketle
    return {
        "sinyaller": pd.concat(tum_sinyaller).to_dict('records') if tum_sinyaller else [],
        "izleme_listesi": izleme_listesi
    }

# --- WEB YOLLARI (ROUTES) ---
@app.route('/')
def index():
    veriler = sinyal_tara()
    return render_template_string(HTML_TEMPLATE, 
                                 sinyaller=veriler["sinyaller"], 
                                 fiyatlar=veriler["izleme_listesi"])

if __name__ == '__main__':
    print("Sunucu başlatılıyor... http://127.0.0.1:5000 adresine gidin.")
    app.run(debug=True, port=5000)