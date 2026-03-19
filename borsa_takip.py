from flask import Flask, render_template_string
import yfinance as yf
import pandas as pd
import ta

app = Flask(__name__)

# HTML Şablonu 
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Borsa Sinyal Takip</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
</head>
<body class="bg-light">
    <div class="container mt-5">
        <h2 class="mb-4 text-center"> Teknik Alim Sinyalleri</h2>
        <div class="card shadow">
            <div class="card-body">
                {% if sinyaller %}
                    <table class="table table-hover">
                        <thead class="table-dark">
                            <tr>
                                <th>Tarih</th>
                                <th>Hisse</th>
                                <th>Fiyat</th>
                                <th>RSI</th>
                                <th>MACD</th>
                                <th>Signal</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for row in sinyaller %}
                            <tr>
                                <td>{{ row['Date'].strftime('%Y-%m-%d') }}</td>
                                <td><strong>{{ row['ticker'] }}</strong></td>
                                <td>{{ "%.2f"|format(row['Close']) }}</td>
                                <td>{{ "%.2f"|format(row['rsi']) }}</td>
                                <td>{{ "%.4f"|format(row['macd']) }}</td>
                                <td>{{ "%.4f"|format(row['macd_signal']) }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                {% else %}
                    <div class="alert alert-warning text-center">Şu an kriterlere uygun bir sinyal bulunmuyor.</div>
                {% endif %}
            </div>
        </div>
        <p class="text-muted mt-3 text-center"><small>Veriler Yahoo Finance üzerinden anlık çekilmektedir.</small></p>
    </div>
</body>
</html>
"""

def sinyal_tara():
    tickers = ["TUPRS.IS", "SISE.IS", "KRDMD.IS", "ASELS.IS", "THYAO.IS"]
    tum_sinyaller = []

    for ticker in tickers:
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        if df.empty:
            continue

        # Veriyi hazırla
        close = df["Close"].astype(float).squeeze()
        volume = df["Volume"].astype(float).squeeze()

        # İndikatörler
        df["rsi"] = ta.momentum.RSIIndicator(close=close, window=14).rsi()
        macd = ta.trend.MACD(close=close)
        df["macd"] = macd.macd()
        df["macd_signal"] = macd.macd_signal()
        df["ema50"] = ta.trend.EMAIndicator(close=close, window=50).ema_indicator()
        df["ema200"] = ta.trend.EMAIndicator(close=close, window=200).ema_indicator()
        df["volume_ma20"] = volume.rolling(window=20).mean()

        # Alım Koşulu
        buy_signal_series = (
            (df["rsi"] < 45) & 
            (df["macd"] > df["macd_signal"]) &
            (close > df["ema50"]) &
            (df["ema50"] > df["ema200"]) &
            (volume > df["volume_ma20"])
        )

        df["buy_signal"] = buy_signal_series
        sinyalli_gunler = df[df["buy_signal"]].copy()

        if not sinyalli_gunler.empty:
            sinyalli_gunler["ticker"] = ticker
            tum_sinyaller.append(sinyalli_gunler.tail(1).reset_index())

    if tum_sinyaller:
        return pd.concat(tum_sinyaller).to_dict('records')
    return []

@app.route('/')
def index():
    veriler = sinyal_tara()
    return render_template_string(HTML_TEMPLATE, sinyaller=veriler)

if __name__ == '__main__':
    app.run(debug=True, port=5000)