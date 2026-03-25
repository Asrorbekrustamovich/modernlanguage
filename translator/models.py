from django.db import models
from django.contrib.auth.models import User

class TranslationResult(models.Model):
    original_image = models.ImageField(upload_to='translations/images/')
    result_markdown = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Translation on {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        ordering = ['-created_at']
