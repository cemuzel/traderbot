from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import google.generativeai as genai
import yfinance as yf
from tradingview_ta import TA_Handler, Interval, Exchange
from tefas import Crawler
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv

# Load env variables (for local dev)
load_dotenv()

# Setup Flask to serve static files and templates
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app) 

# --- AYARLAR ---
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    print("UYARI: API_KEY bulunamadı! .env dosyasını veya environment variable'ı kontrol edin.")

genai.configure(api_key=API_KEY)

# --- HELPER FUNCTIONS ---
def get_tradingview_analysis(symbol):
    try:
        # BIST hisseleri için
        if ".IS" in symbol:
            clean_symbol = symbol.replace(".IS", "")
            exchange = "BIST"
        else:
            clean_symbol = symbol
            exchange = "BIST" # Varsayılan

        handler = TA_Handler(
            symbol=clean_symbol,
            screener="turkey",
            exchange=exchange,
            interval=Interval.INTERVAL_1_DAY
        )
        analysis = handler.get_analysis()
        return {
            "summary": analysis.summary, 
            "indicators": analysis.indicators
        }
    except Exception as e:
        print(f"TradingView Hatası: {e}")
        return None

def get_tefas_data(fund_code):
    try:
        crawler = Crawler()
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=20)).strftime("%Y-%m-%d")
        
        print(f"TEFAS Verisi Çekiliyor: {fund_code} ({start_date} - {end_date})")
        
        result = crawler.fetch(start=start_date, end=end_date)
        
        if result is None or result.empty:
            print("TEFAS boş yanıt döndü.")
            return None

        fund_data = result[result['code'] == fund_code]
        
        if fund_data.empty:
            print(f"TEFAS: {fund_code} için veri bulunamadı.")
            return None
            
        latest_price = fund_data.iloc[-1]['price']
        history = fund_data['price'].tolist() 
        
        print(f"TEFAS Başarılı: {fund_code} Fiyat: {latest_price}")
        return {
            "price": latest_price,
            "history": history
        }
    except Exception as e:
        print(f"TEFAS Hatası Detaylı: {e}")
        return None

# --- ROUTES ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analiz')
def analiz_et():
    # Parametreler: hisse=KOD&tur=hisse|fon
    symbol = request.args.get('hisse', 'THYAO.IS').upper()
    tur = request.args.get('tur', 'hisse') # Varsayılan hisse
    
    print(f"İstek: {symbol} ({tur})")
    
    try:
        son_fiyat = 0
        history_data = []
        tv_summary = "Veri yok"
        
        if tur == 'hisse':
            # 1. YFinance
            if not symbol.endswith(".IS"):
                symbol += ".IS"
            stock = yf.Ticker(symbol)
            hist = stock.history(period="1mo")
            if hist.empty:
                 return jsonify({"hata": "Borsa verisi bulunamadı."}), 400
            son_fiyat = hist['Close'].iloc[-1]
            history_data = hist['Close'].tolist()
            
            # 2. TradingView
            tv_data = get_tradingview_analysis(symbol)
            if tv_data:
                tv_summary = json.dumps(tv_data['summary']) 
                
            prompt_context = f"""
            Hisse: {symbol}
            Güncel Fiyat: {son_fiyat:.2f} TL
            TradingView Teknik Sinyalleri: {tv_summary}
            Son 1 aylık kapanışlar: {history_data}
            """
            
        else: # FON
            # 1. TEFAS
            fund_res = get_tefas_data(symbol)
            if not fund_res:
                return jsonify({"hata": "Fon verisi bulunamadı (Tefas)."}), 400
                
            son_fiyat = fund_res['price']
            history_data = fund_res['history']
            
            prompt_context = f"""
            Yatırım Fonu Kodu: {symbol}
            Güncel Fiyat: {son_fiyat} TL
            Son 1 aylık fiyat hareketleri: {history_data}
            Bu bir yatırım fonudur. Riski ve getirisi buna göre değerlendirilmelidir.
            """

        # 3. Gemini Prompt (Ortak)
        prompt = f"""
        Sen uzman bir finans analistisin. 
        Aşağıdaki verilere göre bir analiz yap.
        
        VERİLER:
        {prompt_context}
        
        GÖREV:
        Bu verilere bakarak yatırımcı için karar desteği ver.
        Cevabını SADECE aşağıdaki JSON formatında ver, başka metin ekleme:
        {{
            "recommendation": "GÜÇLÜ AL" | "AL" | "TUT" | "SAT" | "GÜÇLÜ SAT",
            "risk_level": "Düşük" | "Orta" | "Yüksek" | "Çok Yüksek",
            "risk_score": 0-100 arası sayı (0=Düşük, 100=Yüksek risk),
            "forecast": "Kısa ve orta vadeli beklenti (2-3 cümle)",
            "key_points": [
                "Önemli tespit 1",
                "Önemli tespit 2",
                "Önemli tespit 3"
            ]
        }}
        """
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        
        cleaned_response = response.text.replace('```json', '').replace('```', '').strip()
        analysis_data = json.loads(cleaned_response)
        
        return jsonify({
            "hisse": symbol,
            "fiyat": f"{son_fiyat:.2f}",
            "tur": tur,
            "data": analysis_data
        })
        
    except Exception as e:
        print("Sunucu Hatası:", e)
        return jsonify({"hata": str(e)}), 500

@app.route('/portfolio-analiz', methods=['POST'])
def portfolio_analiz():
    try:
        data = request.json
        assets = data.get('assets', [])
        
        if not assets:
            return jsonify({"hata": "Liste boş"}), 400
            
        # Toplu Veri Toplama
        portfolio_summary = []
        
        print(f"Portfolyo Analizi Başlıyor: {len(assets)} varlık")
        
        for asset in assets:
            item_data = {}
            if ".IS" in asset or len(asset) > 3: # Stock assumption
                try:
                    ticker = yf.Ticker(asset)
                    hist = ticker.history(period="5d")
                    if not hist.empty:
                        change = ((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100
                        item_data = {
                            "code": asset,
                            "type": "Stock",
                            "price": hist['Close'].iloc[-1],
                            "weekly_change_pct": change
                        }
                except:
                    pass
            else: # Fund assumption
                try:
                    c = Crawler()
                    end = datetime.now().strftime("%Y-%m-%d")
                    start = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
                    res = c.fetch(start=start, end=end) # columns removed for safety
                    f_data = res[res['code'] == asset]
                    if not f_data.empty:
                        p_start = f_data.iloc[0]['price']
                        p_end = f_data.iloc[-1]['price']
                        change = ((p_end - p_start) / p_start) * 100
                        item_data = {
                            "code": asset,
                            "type": "Fund",
                            "price": p_end,
                            "weekly_change_pct": change
                        }
                except:
                    pass
            
            if item_data:
                portfolio_summary.append(item_data)
        
        # Gemini Prompt
        prompt = f"""
        Bu bir portfolyo analizidir. Aşağıdaki varlık listesini bir bütün olarak değerlendir.
        
        VARLIKLAR:
        {json.dumps(portfolio_summary, indent=2)}
        
        GÖREV:
        Bu portföyün çeşitliliğini, risk durumunu ve potansiyelini yorumla.
        Cevabı JSON formatında ver:
        {{
            "general_score": 0-100 (Genel Sağlık Skoru),
            "diversity_status": "İyi" | "Orta" | "Kötü" (Çeşitlilik Durumu),
            "risk_assessment": "Portföyün genel risk değerlendirmesi",
            "strategy_advice": "Bu portföyü iyileştirmek için 2-3 cümlelik stratejik tavsiye",
            "star_asset": "En çok potansiyel vadeden varlık kodu"
        }}
        """
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        cleaned = response.text.replace('```json', '').replace('```', '').strip()
        result = json.loads(cleaned)
        
        return jsonify(result)

    except Exception as e:
        print("Portfolyo Hatası:", e)
        return jsonify({"hata": str(e)}), 500

if __name__ == '__main__':
    # Local dev run
    app.run(debug=True, port=5000)