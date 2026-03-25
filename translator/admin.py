from django.contrib import admin
from .models import TranslationResult

@admin.register(TranslationResult)
class TranslationResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('result_markdown',)
    readonly_fields = ('created_at',)
