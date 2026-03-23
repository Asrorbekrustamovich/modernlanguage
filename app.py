import os
import markdown
from flask import Flask, render_template, request, redirect, flash, url_for
from werkzeug.utils import secure_filename
import google.generativeai as genai
from PIL import Image

app = Flask(__name__)
app.secret_key = 'super_secret_key'

# Fayllar saqlanadigan papka
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Gemini API sozlamalari
api_key = os.environ.get('GEMINI_API_KEY')
if api_key:
    genai.configure(api_key=api_key)
    
model_name = 'gemini-1.5-pro' # Rasm o'qish va tarjima uchun eng yaxshisi

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
                # Rasmni ochish va Gemini yordamida o'qish
                img = Image.open(filepath)
                model = genai.GenerativeModel(model_name)
                
                prompt = """
                Quyidagi rasmda eski yozuvdagi (arab, fors yoki eski o'zbek/chig'atoy tilidagi nastaliq xati) hujjat yoki qog'oz parchasi bor.
                Iltimos, shu matnni o'qib, uni hozirgi zamonaviy o'zbek tiliga o'girib ber.
                Natijani quyidagi tartibda chiroyli qilib yoz:
                1. **Asl matn:** O'qilishi (transkripsiyasi).
                2. **Tarjimasi:** Zamonaviy o'zbek tilidagi tarjimasi va batafsil ma'nosi.
                3. **Qo'shimcha izohlar:** Agar matnda tarixiy atamalar yoki tushunarsiz so'zlar bo'lsa, ularni izohlab ber.
                P.S. Asosan eski yozuvga (qog'ozdagi yozuvga) e'tibor qarating, fondagi lotincha yozuvlarga e'tibor qaratmang.
                """
                
                response = model.generate_content([prompt, img])
                result_html = markdown.markdown(response.text)
                
                return render_template('result.html', filename=filename, result=result_html)
            except Exception as e:
                flash(f"Xatolik yuz berdi: {str(e)}", "error")
                return redirect(request.url)
        else:
            flash("Faqat rasm fayllari ruxsat etilgan! (png, jpg, jpeg, gif, webp)", "error")
            return redirect(request.url)
                
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
