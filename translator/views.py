import os
import markdown as md
import requests
import base64
import io
import re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse
from django.conf import settings
from fpdf import FPDF
from .models import TranslationResult

# Gemini API settings
model_name = 'gemini-1.5-flash' # Barqaror va tezkor model

@login_required
def index(request):
    if request.method == 'POST':
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            messages.error(request, "GEMINI_API_KEY topilmadi!")
            return redirect('index')
            
        file = request.FILES.get('file')
        if not file:
            messages.error(request, "Fayl tanlanmadi")
            return redirect('index')
        try:
            # Modelni tanlash
            model_name = request.POST.get('model_name', 'gemini-1.5-flash')
            
            # Reverting to requests approach as SDK version is outdated
            result_obj = TranslationResult(original_image=file)
            result_obj.save()
            filepath = result_obj.original_image.path
            
            with open(filepath, "rb") as f:
                base64_data = base64.b64encode(f.read()).decode('utf-8')
            
            headers = {'Content-Type': 'application/json'}
            data = {
                "contents": [{
                    "parts": [
                        {"text": "Ushbu rasmda yozilgan matnlarni o'qing, ularni zamonaviy o'zbek tiliga tarjima qiling va chuqur tahlilini bering. Markdown formatida chop eting."},
                        {"inline_data": {"mime_type": "image/jpeg", "data": base64_data}}
                    ]
                }],
                "generationConfig": {"temperature": 0.4}
            }
            
            # Request approach
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                resp_json = response.json()
                candidates = resp_json.get('candidates', [])
                if candidates and 'content' in candidates[0]:
                    text = candidates[0]['content'].get('parts', [])[0].get('text', '')
                    result_obj.result_markdown = text
                    result_obj.save()
                    
                    result_html = md.markdown(text)
                    return render(request, 'result.html', {
                        'result_obj': result_obj,
                        'result_html': result_html,
                    })
                else:
                    raise Exception("Noma'lum javob formati")
            else:
                error_msg = response.json().get('error', {}).get('message', 'Noma\'lum xatolik')
                raise Exception(f"API Xatosi (Kodi {response.status_code}): {error_msg}")
                
        except Exception as e:
            messages.error(request, f"Xatolik yuz berdi: {str(e)}")
            return redirect('index')
            
    return render(request, 'index.html')

@login_required
def history(request):
    results = TranslationResult.objects.all()
    return render(request, 'history.html', {'results': results})

@login_required
def result_detail(request, pk):
    result_obj = get_object_or_404(TranslationResult, pk=pk)
    result_html = md.markdown(result_obj.result_markdown)
    return render(request, 'result.html', {
        'result_obj': result_obj,
        'result_html': result_html,
    })

@login_required
def download_pdf(request, pk):
    result_obj = get_object_or_404(TranslationResult, pk=pk)
    result_text = result_obj.result_markdown
    
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # --- DIZAYN ELEMENTLARI ---
        pdf.set_fill_color(245, 240, 225)
        pdf.rect(0, 0, 210, 297, 'F')
        
        pdf.set_draw_color(93, 64, 55)
        pdf.set_line_width(1.5)
        pdf.rect(5, 5, 200, 287)
        pdf.set_line_width(0.5)
        pdf.rect(7, 7, 196, 283)
        
        pdf.set_font("Helvetica", 'B', 22)
        pdf.set_text_color(93, 64, 55)
        pdf.ln(15)
        pdf.cell(0, 15, text="TARIXIY MATN TARJIMASI", ln=True, align='C')
        
        pdf.set_font("Helvetica", size=14)
        pdf.cell(0, 10, text="~ ~ ~ ~ * * * ~ ~ ~ ~", ln=True, align='C')
        pdf.ln(10)
        
        # --- MATNNI TOZALASH ---
        clean_text = re.sub(r'<[^>]+>', '', result_text)
        clean_text = re.sub(r'\*+\s?', '', clean_text)
        clean_text = re.sub(r'\n{3,}', '\n\n', clean_text)
        clean_text = clean_text.replace('ʻ', "'").replace('ʼ', "'").replace('’', "'").replace('‘', "'")
        
        safe_text = ""
        for char in clean_text:
            try:
                char.encode('latin-1')
                safe_text += char
            except UnicodeEncodeError:
                continue
        
        pdf.set_left_margin(15)
        pdf.set_right_margin(15)
        
        sections = safe_text.split('\n\n')
        for section in sections:
            stripped = section.strip()
            if not stripped: continue
                
            if any(key in stripped for key in ["Asl matn", "Tarjimasi", "Izohlar", "Muallif", "ma'nosi", "tahlili"]):
                pdf.set_font("Helvetica", 'B', 14)
                pdf.set_text_color(93, 64, 55)
                pdf.multi_cell(0, 10, text=stripped)
                pdf.ln(2)
            else:
                pdf.set_font("Helvetica", size=12)
                pdf.set_text_color(40, 40, 40)
                pdf.multi_cell(0, 8, text=stripped)
                pdf.ln(6)
        
        pdf.set_y(-35)
        pdf.set_text_color(93, 64, 55)
        pdf.cell(0, 10, text="- - - - - * * * - - - - -", ln=True, align='C')
        
        pdf.set_y(-25)
        pdf.set_font("Helvetica", 'I', 8)
        pdf.cell(0, 10, text="Tarixiy Matn Tarjimoni orqali yaratildi", align='C')
        
        pdf_bytes = pdf.output()
        
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="translation_{pk}.pdf"'
        return response
    except Exception as e:
        messages.error(request, f"PDF yaratishda xatolik: {str(e)}")
        return redirect('result_detail', pk=pk)

@login_required
@require_POST
def delete_result(request, pk):
    result_obj = get_object_or_404(TranslationResult, pk=pk)
    if result_obj.original_image:
        if os.path.isfile(result_obj.original_image.path):
            os.remove(result_obj.original_image.path)
    
    result_obj.delete()
    messages.success(request, "Tarjima muvaffaqiyatli o'chirildi.")
    return redirect('history')
