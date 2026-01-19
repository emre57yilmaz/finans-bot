from flask import Flask, jsonify
from flask_cors import CORS
import requests
import feedparser
import datetime
import random
import urllib.parse  # Link dönüştürücü kütüphane

app = Flask(__name__)
CORS(app)

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

ASSETS = {
    "USD": {"symbol": "TRY=X", "name": "Dolar", "type": "currency"},
    "EUR": {"symbol": "EURTRY=X", "name": "Euro", "type": "currency"},
    "BTC": {"symbol": "BTC-USD", "name": "Bitcoin", "type": "crypto"},
    "ETH": {"symbol": "ETH-USD", "name": "Ethereum", "type": "crypto"},
    "GOLD": {"symbol": "GC=F", "name": "Altın", "type": "metal_ounce"},
    "SILVER": {"symbol": "SI=F", "name": "Gümüş", "type": "metal_ounce"},
    "PLATINUM": {"symbol": "PL=F", "name": "Platin", "type": "metal_ounce"},
    "COPPER": {"symbol": "HG=F", "name": "Bakır", "type": "metal_lbs"},
    "ALUMINUM": {"symbol": "ALI=F", "name": "Alüminyum", "type": "metal_ton"}
}

def get_price(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        resp = requests.get(url, headers=HEADERS, timeout=4)
        return float(resp.json()['chart']['result'][0]['meta']['regularMarketPrice'])
    except: return 0.0

def get_data():
    data = {}
    usd = get_price("TRY=X") or 34.50
    
    for key, info in ASSETS.items():
        raw = get_price(info['symbol'])
        price_tl = 0
        if info['type'] == 'currency': price_tl = raw
        elif info['type'] == 'crypto': price_tl = raw * usd
        elif info['type'] == 'metal_ounce': price_tl = (raw / 31.1035) * usd
        elif info['type'] == 'metal_lbs': price_tl = (raw * 2.20462) * usd
        elif info['type'] == 'metal_ton': price_tl = (raw * usd) / 1000
        
        data[key] = {"name": info["name"], "price_base_tl": price_tl, "raw": raw}
    return data, usd

def get_news():
    # Güvenilir RSS Kaynakları
    sources = [
        {"url": "https://www.trthaber.com/xml_mobile.php?tur=xml_genel&kategori=ekonomi", "name": "TRT Haber"},
        {"url": "https://feeds.bbci.co.uk/turkce/rss.xml", "name": "BBC Türkçe"},
        {"url": "https://www.ntv.com.tr/ekonomi.rss", "name": "NTV"},
        {"url": "https://www.donanimhaber.com/rss/tum/", "name": "DonanımHaber"}
    ]
    random.shuffle(sources)
    
    for source in sources:
        try:
            feed = feedparser.parse(source['url'])
            if feed.entries:
                entry = feed.entries[0]
                headline = entry.title
                
                # --- İŞ YERİ HİLESİ BURADA ---
                # Haberin orijinal linkini ALMIYORUZ.
                # Başlığı Google Aramasına çeviriyoruz.
                # Örn: "Dolar Rekor Kırdı" -> google.com/search?q=Dolar+Rekor+Kırdı&tbm=nws
                
                encoded_query = urllib.parse.quote(headline)
                # tbm=nws parametresi Google'ın "Haberler" sekmesini açar
                google_link = f"https://www.google.com/search?q={encoded_query}&tbm=nws"
                
                return {
                    "headline": headline, 
                    "url": google_link,  # <-- Tıklayınca Google açılacak
                    "source": source['name']
                }
        except: continue
        
    return {"headline": "Veri akışı bekleniyor...", "url": "https://www.google.com/finance", "source": "Sistem"}

@app.route('/api/full_data')
def full_data():
    assets, usd = get_data()
    return jsonify({"assets": assets, "usd_rate": usd, "news": get_news(), "timestamp": datetime.datetime.now().strftime("%H:%M")})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
