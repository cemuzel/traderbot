<<<<<<< HEAD
import os
from flask import Flask, request, jsonify
from flask_cors import CORS  # Yeni ekledik
import google.generativeai as genai
import yfinance as yf

app = Flask(__name__)
CORS(app) # Tüm sitelerden gelen isteklere izin ver (Kendi siten erişebilsin diye)

# API Anahtarını Render'ın ayarlarından alacak
GENAI_API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=GENAI_API_KEY)

@app.route('/')
def home():
    return "Borsa Botu Calisiyor! Analiz icin endpoint: /analiz"

@app.route('/analiz')
def analiz_et():
    symbol = request.args.get('hisse', 'THYAO.IS') 
    
    try:
        # 1. Hisseyi Yfinance'dan Çek
        stock = yf.Ticker(symbol)
        hist = stock.history(period="1mo")
        
        if hist.empty:
             return jsonify({"hata": "Veri bulunamadı. Hisse kodunu kontrol et (Örn: GARAN.IS)"}), 400

        son_fiyat = hist['Close'].iloc[-1]
        
        # 2. Gemini İçin Veri Hazırla
        prompt = f"""
        Sen profesyonel bir borsa uzmanısın. 
        Hisse: {symbol}
        Son Fiyat: {son_fiyat:.2f}
        Son 1 aylık kapanış trendi: {hist['Close'].tolist()}
        
        Bu verilere dayanarak çok kısa bir teknik analiz yap.
        Yatırım tavsiyesi olmadığını belirterek AL/SAT/BEKLE yönünde görüş bildir.
        Cevabın HTML formatında değil, düz metin olsun. Türkçe konuş.
        """
        
        # 3. Gemini'ye Sor
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        
        return jsonify({
            "hisse": symbol,
            "fiyat": f"{son_fiyat:.2f}",
            "analiz": response.text
        })
        
    except Exception as e:
        return jsonify({"hata": str(e)}), 500

if __name__ == '__main__':
=======
import os
from flask import Flask, request, jsonify
from flask_cors import CORS  # Yeni ekledik
import google.generativeai as genai
import yfinance as yf

app = Flask(__name__)
CORS(app) # Tüm sitelerden gelen isteklere izin ver (Kendi siten erişebilsin diye)

# API Anahtarını Render'ın ayarlarından alacak
GENAI_API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=GENAI_API_KEY)

@app.route('/')
def home():
    return "Borsa Botu Calisiyor! Analiz icin endpoint: /analiz"

@app.route('/analiz')
def analiz_et():
    symbol = request.args.get('hisse', 'THYAO.IS') 
    
    try:
        # 1. Hisseyi Yfinance'dan Çek
        stock = yf.Ticker(symbol)
        hist = stock.history(period="1mo")
        
        if hist.empty:
             return jsonify({"hata": "Veri bulunamadı. Hisse kodunu kontrol et (Örn: GARAN.IS)"}), 400

        son_fiyat = hist['Close'].iloc[-1]
        
        # 2. Gemini İçin Veri Hazırla
        prompt = f"""
        Sen profesyonel bir borsa uzmanısın. 
        Hisse: {symbol}
        Son Fiyat: {son_fiyat:.2f}
        Son 1 aylık kapanış trendi: {hist['Close'].tolist()}
        
        Bu verilere dayanarak çok kısa bir teknik analiz yap.
        Yatırım tavsiyesi olmadığını belirterek AL/SAT/BEKLE yönünde görüş bildir.
        Cevabın HTML formatında değil, düz metin olsun. Türkçe konuş.
        """
        
        # 3. Gemini'ye Sor
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        
        return jsonify({
            "hisse": symbol,
            "fiyat": f"{son_fiyat:.2f}",
            "analiz": response.text
        })
        
    except Exception as e:
        return jsonify({"hata": str(e)}), 500

if __name__ == '__main__':
>>>>>>> f3d89f504bce7d40698263d1febbc2ea0e24b7f5
    app.run(debug=True)