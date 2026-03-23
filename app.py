import os
import markdown
import requests
import base64
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, flash, url_for
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
app.secret_key = 'super_secret_key'

# Fayllar saqlanadigan papka
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Gemini API sozlamalari
api_key = os.environ.get('GEMINI_API_KEY')
    
model_name = 'gemini-2.5-flash' # Rasm o'qish va tarjima uchun

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if not api_key:
            flash("GEMINI_API_KEY tizim o'zgaruvchisi topilmadi! Iltimos, sozlang.", "error")
            return redirect(request.url)
            
        if 'file' not in request.files:
            flash("Fayl tanlanmadi", "error")
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash("Fayl tanlanmadi", "error")
            return redirect(request.url)
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            try:
                prompt = """
                Quyidagi rasmda eski yozuvdagi (arab, fors yoki eski o'zbek/chig'atoy tilidagi nastaliq xati) hujjat yoki qog'oz parchasi bor.
                Iltimos, shu matnni o'qib, uni hozirgi zamonaviy o'zbek tiliga o'girib ber.
                Natijani quyidagi tartibda chiroyli qilib yoz:
                1. **Asl matn:** O'qilishi (transkripsiyasi).
                2. **Tarjimasi:** Zamonaviy o'zbek tilidagi tarjimasi va batafsil ma'nosi.
                3. **Qo'shimcha izohlar:** Agar matnda tarixiy atamalar yoki tushunarsiz so'zlar bo'lsa, ularni izohlab ber.
                P.S. Asosan eski yozuvga (qog'ozdagi yozuvga) e'tibor qarating, fondagi lotincha yozuvlarga e'tibor qaratmang.
                """
                
                base64_image = encode_image(filepath)
                mime_type = "image/jpeg"
                ext = filename.lower().rsplit('.', 1)[1]
                if ext == 'png':
                    mime_type = "image/png"
                elif ext == 'webp':
                    mime_type = "image/webp"
                elif ext == 'gif':
                    mime_type = "image/gif"

                headers = {'Content-Type': 'application/json'}
                data = {
                    "contents": [{
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": base64_image
                                }
                            }
                        ]
                    }],
                    "generationConfig": {
                        "temperature": 0.4
                    }
                }
                
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                response = requests.post(url, headers=headers, json=data)
                
                if response.status_code == 200:
                    resp_json = response.json()
                    candidates = resp_json.get('candidates', [])
                    if candidates and 'content' in candidates[0]:
                        parts = candidates[0]['content'].get('parts', [])
                        text = parts[0].get('text', '')
                        result_html = markdown.markdown(text)
                        return render_template('result.html', filename=filename, result=result_html)
                    else:
                        raise Exception("Noma'lum javob formati")
                else:
                    error_msg = response.json().get('error', {}).get('message', 'Noma\'lum xatolik')
                    raise Exception(f"API Xatosi (Kodi {response.status_code}): {error_msg}")
                    
            except Exception as e:
                flash(f"Xatolik yuz berdi: {str(e)}", "error")
                return redirect(request.url)
        else:
            flash("Faqat rasm fayllari ruxsat etilgan! (png, jpg, jpeg, gif, webp)", "error")
            return redirect(request.url)
                
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
