from django.db import models
from django.contrib.auth.models import User

class TranslationResult(models.Model):
    original_image = models.ImageField(upload_to='translations/images/', verbose_name="Asl rasm")
    result_markdown = models.TextField(verbose_name="Tarjima natijasi (Markdown)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqti")

    def __str__(self):
        return f"Tarjima: {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        verbose_name = "Tarjima natijasi"
        verbose_name_plural = "Tarjima natijalari"
        ordering = ['-created_at']
