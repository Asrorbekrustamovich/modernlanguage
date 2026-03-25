import os
import markdown
import requests
import base64
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from fpdf import FPDF
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    flash,
    url_for,
    send_file,
    session,
)
import io

load_dotenv()

app = Flask(__name__)
app.secret_key = "super_secret_key"

# Fayllar saqlanadigan papka
UPLOAD_FOLDER = os.path.join("static", "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Gemini API sozlamalari
api_key = os.environ.get("GEMINI_API_KEY")

model_name = "gemini-2.5-flash"  # Rasm o'qish va tarjima uchun

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "pdf"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def encode_file(file_path):
    with open(file_path, "rb") as file:
        return base64.b64encode(file.read()).decode("utf-8")


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if not api_key:
            flash(
                "GEMINI_API_KEY tizim o'zgaruvchisi topilmadi! Iltimos, sozlang.",
                "error",
            )
            return redirect(request.url)

        if "file" not in request.files:
            flash("Fayl tanlanmadi", "error")
            return redirect(request.url)

        file = request.files["file"]
        if file.filename == "":
            flash("Fayl tanlanmadi", "error")
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            try:
                prompt = """
                Siz qadimiy qo'lyozmalar, hujjatlar va tarixiy matnlar bo'yicha mutaxassis emassiz.
                Quyidagi hujjatda (rasm yoki PDF) eski yozuvdagi (arab, fors yoki eski o'zbek/chig'atoy tilidagi nastaliq xati) matnlar bor.
                
                Vazifangiz:
                1. Matnni sinchiklab o'qib, uning **transkripsiyasini** (o'qilishini) yozing.
                2. Matnni hozirgi zamonaviy o'zbek tiliga **so'zma-so'z va badiiy tarjima** qiling.
                3. **MA'NOSI VA TAHLILI:** Bu qismga alohida e'tibor bering. Matnning umumiy mazmuni, maqsadi, muallif nima demoqchi bo'lgani va matnning tarixiy/madaniy ahamiyatini chuqur tushuntirib bering.
                4. **Tarixiy atamalar:** Matndagi qadimiy so'zlar va iboralarning izohini bering.

                Natijani chiroyli Markdown formatida quyidagi tartibda chiqaring:
                ### 📜 Asl matn (O'qilishi)
                [Transkripsiya bu yerda]

                ### ✍️ Zamonaviy o'zbek tilidagi tarjimasi
                [Tarjima bu yerda]

                ### 💡 Batafsil ma'nosi va chuqur tahlili
                [Bu yerda matnning mazmuni va mohiyatini juda batafsil tushuntirib bering]

                ### 📚 Tarixiy atamalar va izohlar
                [Izohlar bu yerda]

                P.S. Hujjatdagi har bir so'z va belgiga e'tibor bering.
                """

                base64_data = encode_file(filepath)
                ext = filename.lower().rsplit(".", 1)[1]

                mime_type = "image/jpeg"
                if ext == "png":
                    mime_type = "image/png"
                elif ext == "webp":
                    mime_type = "image/webp"
                elif ext == "gif":
                    mime_type = "image/gif"
                elif ext == "pdf":
                    mime_type = "application/pdf"

                headers = {"Content-Type": "application/json"}
                data = {
                    "contents": [
                        {
                            "parts": [
                                {"text": prompt},
                                {
                                    "inline_data": {
                                        "mime_type": mime_type,
                                        "data": base64_data,
                                    }
                                },
                            ]
                        }
                    ],
                    "generationConfig": {"temperature": 0.4},
                }

                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                response = requests.post(url, headers=headers, json=data)

                if response.status_code == 200:
                    resp_json = response.json()
                    candidates = resp_json.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        text = parts[0].get("text", "")
                        result_html = markdown.markdown(text)
                        return render_template(
                            "result.html",
                            filename=filename,
                            result=result_html,
                            is_pdf=(ext == "pdf"),
                        )
                    else:
                        raise Exception("Noma'lum javob formati")
                else:
                    error_msg = (
                        response.json()
                        .get("error", {})
                        .get("message", "Noma'lum xatolik")
                    )
                    raise Exception(
                        f"API Xatosi (Kodi {response.status_code}): {error_msg}"
                    )

            except Exception as e:
                flash(f"Xatolik yuz berdi: {str(e)}", "error")
                return redirect(request.url)
        else:
            flash(
                "Faqat rasm va PDF fayllari ruxsat etilgan! (png, jpg, jpeg, gif, webp, pdf)",
                "error",
            )
            return redirect(request.url)

    return render_template("index.html")


@app.route("/download_pdf", methods=["POST"])
def download_pdf():
    result_text = request.form.get("result_text", "")
    filename = request.form.get("filename", "tarjima_natijasi.pdf")

    if not result_text:
        flash("Yuklab olish uchun ma'lumot topilmadi", "error")
        return redirect(url_for("index"))

    # PDF yaratish
    try:
        # fpdf2 ishlatamiz
        pdf = FPDF()
        pdf.add_page()

        # --- DIZAYN ELEMENTLARI ---
        # Orqa fon (pergament rang - och krem)
        pdf.set_fill_color(245, 240, 225)
        pdf.rect(0, 0, 210, 297, "F")

        # Ramka (Double border)
        pdf.set_draw_color(93, 64, 55)  # Leather color
        pdf.set_line_width(1.5)
        pdf.rect(5, 5, 200, 287)
        pdf.set_line_width(0.5)
        pdf.rect(7, 7, 196, 283)

        # Sarlavha ornamenti
        pdf.set_font("Helvetica", "B", 22)
        pdf.set_text_color(93, 64, 55)
        pdf.ln(15)
        pdf.cell(0, 15, text="TARIXIY MATN TARJIMASI", ln=True, align="C")

        pdf.set_font("Helvetica", size=14)
        pdf.cell(0, 10, text="~ ~ ~ ~ * * * ~ ~ ~ ~", ln=True, align="C")
        pdf.ln(10)

        # --- MATNNI TOZALASH ---
        import re

        # Barcha HTML teglaridan butunlay tozalash
        clean_text = re.sub(r"<[^>]+>", "", result_text)
        # Markdown belgilaridan tozalash
        clean_text = re.sub(r"\*+\s?", "", clean_text)
        # Ortiqcha bo'sh joylar
        clean_text = re.sub(r"\n{3,}", "\n\n", clean_text)

        # Maxsus o'zbekcha belgilarni almashtirish
        clean_text = (
            clean_text.replace("ʻ", "'")
            .replace("ʼ", "'")
            .replace("’", "'")
            .replace("‘", "'")
        )

        # Latin-1 diapazonidagi belgilarni qolidirish
        safe_text = ""
        for char in clean_text:
            try:
                char.encode("latin-1")
                safe_text += char
            except UnicodeEncodeError:
                continue

        # --- ASOSIY MATN ---
        pdf.set_left_margin(15)
        pdf.set_right_margin(15)

        sections = safe_text.split("\n\n")
        for section in sections:
            stripped = section.strip()
            if not stripped:
                continue

            # Sarlavhalarni aniqlash
            if any(
                key in stripped
                for key in [
                    "Asl matn",
                    "Tarjimasi",
                    "Izohlar",
                    "Muallif",
                    "ma'nosi",
                    "tahlili",
                ]
            ):
                pdf.set_font("Helvetica", "B", 14)
                pdf.set_text_color(93, 64, 55)
                pdf.multi_cell(0, 10, text=stripped)
                pdf.ln(2)
            else:
                pdf.set_font("Helvetica", size=12)
                pdf.set_text_color(40, 40, 40)  # To'q kulrang/qora siyoh
                pdf.multi_cell(0, 8, text=stripped)
                pdf.ln(6)

        # Footer ornamenti
        pdf.set_y(-35)
        pdf.set_text_color(93, 64, 55)
        pdf.cell(0, 10, text="- - - - - * * * - - - - -", ln=True, align="C")

        pdf.set_y(-25)
        pdf.set_font("Helvetica", "I", 8)
        pdf.cell(0, 10, text="Tarixiy Matn Tarjimoni orqali yaratildi", align="C")

        # PDF ni xotirada saqlash
        pdf_bytes = pdf.output()

        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"tarjima_{filename}.pdf",
        )
    except Exception as e:
        flash(f"PDF yaratishda xatolik: {str(e)}", "error")
        return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
