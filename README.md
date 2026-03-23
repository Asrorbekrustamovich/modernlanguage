# Tarixiy Matn Tarjimoni

Bu loyiha eski yozuvlarni (arab, fors, chig'atoy tillaridagi nastaliq xati) rasm orqali o'qib, zamonaviy o'zbek tiliga tarjima qilib beruvchi veb-ilovadir. Ilova Python, Flask, Jinja2 va Google Gemini sun'iy intellektidan foydalanadi.

Siz ulagan rasm (masalan eski vaqtga tegishli hujjat) ustidagi yozuvlar generativ model orqali o'qilib (OCR) va matnga aylantirilib, so'ngra hozirgi zamonaviy o'zbek tiliga tarjima qilib beriladi.

## O'rnatish tartibi

1. Kerakli kutubxonalarni o'rnating:
```bash
pip install -r requirements.txt
```

2. Google Gemini API kalitini oling (https://aistudio.google.com/) va uni tizim o'zgaruvchisi (Environment Variable) sifatida saqlang:

Windows (Command Prompt):
```bash
set GEMINI_API_KEY=sizning_api_kalitingiz
```

Windows (PowerShell):
```powershell
$env:GEMINI_API_KEY="sizning_api_kalitingiz"
```

3. Dasturni ishga tushiring:
```bash
python app.py
```

4. Brauzeringizda quyidagi manzilga kiring: http://127.0.0.1:5000
