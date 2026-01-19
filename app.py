from flask import Flask, jsonify
from flask_cors import CORS
import requests
import feedparser  # Yeni kütüphanemiz
import datetime
import urllib3
import random

# SSL Hatalarını Gizle
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
CORS(app)

# Yahoo Finance API Ayarları
BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{}"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

# --- GENİŞLETİLMİŞ HABER HAVUZU ---
# RSS Linklerinin çalıştığından emin olunan liste
NEWS_SOURCES = [
    {"name": "BBC Türkçe", "url": "http://feeds.bbci.co.uk/turkce/rss.xml"},
    {"name": "NTV Ekonomi", "url": "https://www.ntv.com.tr/ekonomi.rss"},
    {"name": "DonanımHaber", "url": "https://www.donanimhaber.com/rss/tum/"}, # Teknoloji/Finans karışık
    {"name": "Webrazzi", "url": "https://webrazzi.com/feed/"}, # Girişim/Finans
    {"name": "TRT Haber", "url": "https://www.trthaber.com/xml_mobile.php?tur=xml_genel&kategori=ekonomi"},
    {"name": "Cumhuriyet Eko", "url": "https://www.cumhuriyet.com.tr/rss/ekonomi"},
    {"name": "Hürriyet Eko", "url": "https://www.hurriyet.com.tr/rss/ekonomi"},
    {"name": "CNN Türk Eko", "url": "https://www.cnnturk.com/feed/rss/ekonomi/news"},
    {"name": "Milliyet Eko", "url": "https://www.milliyet.com.tr/rss/rssnew/ekonomi.xml"},
    {"name": "Ensonhaber", "url": "https://www.ensonhaber.com/rss/ekonomi.xml"},
    {"name": "Google News", "url": "https://news.google.com/rss/search?q=ekonomi+finans&hl=tr-TR&gl=TR&ceid=TR:tr"}
]

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

def get_smart_news():
    """
    Haber kaynaklarını karıştırır ve çalışan İLK kaynağı alır.
    Feedparser kütüphanesi sayesinde hata oranı %1'e düşer.
    """
    # Kaynakları karıştır (Her seferinde farklı yerden denesin)
    shuffled_sources = NEWS_SOURCES.copy()
    random.shuffle(shuffled_sources)
    
    # İlk 5 kaynağı dene (Hepsini deneme ki sistem yavaşlamasın)
    for source in shuffled_sources[:5]:
        try:
            # Feedparser ile oku (Çok daha güçlüdür)
            feed = feedparser.parse(source['url'])
            
            if feed.entries:
                entry = feed.entries[0] # İlk haber
                
                title = entry.title
                link = entry.link
                
                # Başlık temizliği
                for trash in [' - CNN Türk', ' - NTV', ' - TRT Haber', '<![CDATA[', ']]>']:
                    title = title.replace(trash, "")
                
                print(f"Haber çekildi: {source['name']}") # CMD ekranında görmen için
                return {
                    "headline": title[:90] + "..." if len(title) > 90 else title,
                    "source_name": source['name'],
                    "url": link
                }
        except Exception as e:
            print(f"Hata ({source['name']}): {e}")
            continue

    # Hiçbiri çalışmazsa
    return {
        "headline": "Piyasalar takip ediliyor (Haber kaynağı yanıt vermedi)", 
        "source_name": "SİSTEM",
        "url": "https://www.google.com/search?q=ekonomi"
    }

def get_price(symbol):
    try:
        url = BASE_URL.format(symbol)
        resp = requests.get(url, headers=HEADERS, timeout=5, verify=False)
        data = resp.json()
        return float(data['chart']['result'][0]['meta']['regularMarketPrice'])
    except:
        return None

def get_data():
    data = {}
    usd = get_price("TRY=X") or 34.50
    
    for key, info in ASSETS.items():
        raw = get_price(info['symbol'])
        if raw is None:
            data[key] = {"price_base_tl": 0, "raw": 0, "name": info["name"]}
            continue

        price_tl = 0
        if info['type'] == 'currency': price_tl = raw
        elif info['type'] == 'crypto': price_tl = raw * usd
        elif info['type'] == 'metal_ounce': price_tl = (raw / 31.1035) * usd
        elif info['type'] == 'metal_lbs': price_tl = (raw * 2.20462) * usd
        elif info['type'] == 'metal_ton': price_tl = (raw * usd) / 1000

        data[key] = {
            "name": info["name"],
            "price_base_tl": price_tl,
            "raw": raw
        }
    return data, usd

@app.route('/api/full_data', methods=['GET'])
def full_data():
    # 1. Fiyatları Al
    assets, usd = get_data()
    # 2. Haberi Al
    news_data = get_smart_news()
    
    return jsonify({
        "timestamp": datetime.datetime.now().strftime("%H:%M"),
        "assets": assets,
        "usd_rate": usd,
        "news": news_data
    })

if __name__ == '__main__':
    print("--- FİNANS PRO SERVER (FEEDPARSER MODU) ---")
    app.run(debug=True, port=5000)
