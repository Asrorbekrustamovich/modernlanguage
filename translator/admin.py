from django.contrib import admin
from django.contrib.auth.models import User, Group
from .models import TranslationResult

# Foydalanuvchilar va guruhlar nomini o'zbekchaga almashtirish
User._meta.verbose_name = "Foydalanuvchi"
User._meta.verbose_name_plural = "Foydalanuvchilar"
Group._meta.verbose_name = "Guruh"
Group._meta.verbose_name_plural = "Guruhlar"

@admin.register(TranslationResult)
class TranslationResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('result_markdown',)
    readonly_fields = ('created_at',)
