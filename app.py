import os
from flask import Flask, request, jsonify
import google.generativeai as genai
import yfinance as yf

app = Flask(__name__)

# API Anahtarını Render'ın ayarlarından alacak
GENAI_API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=GENAI_API_KEY)

@app.route('/')
def home():
    return "Borsa Botu Calisiyor! Analiz icin: /analiz?hisse=THYAO.IS"

@app.route('/analiz')
def analiz_et():
    symbol = request.args.get('hisse', 'THYAO.IS') # Varsayılan THYAO
    
    try:
        # 1. Hisseyi Yfinance'dan Çek
        stock = yf.Ticker(symbol)
        hist = stock.history(period="1mo")
        son_fiyat = hist['Close'].iloc[-1]
        
        # 2. Gemini İçin Veri Hazırla
        prompt = f"""
        Sen bir finans uzmanısın. Şu teknik verilere bak:
        Hisse: {symbol}
        Son Fiyat: {son_fiyat:.2f}
        Son 1 aylık kapanışlar: {hist['Close'].tolist()}
        
        Bu hisse için kısa vadeli bir teknik analiz yap. 
        Yatırım tavsiyesi olmadığını belirterek AL/SAT/BEKLE yönünde görüş bildir.
        Cevabın Türkçe, kısa ve net olsun.
        """
        
        # 3. Gemini'ye Sor
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        
        return jsonify({
            "hisse": symbol,
            "fiyat": son_fiyat,
            "analiz": response.text
        })
        
    except Exception as e:
        return jsonify({"hata": str(e)})

if __name__ == '__main__':
    app.run(debug=True)