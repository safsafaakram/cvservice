from django.contrib import admin

from .models import CV


@admin.register(CV)
class CVAdmin(admin.ModelAdmin):
    list_display = ("id", "candidate_name", "email", "job_id", "score", "created_at")
    list_filter = ("job_id", "created_at")
    search_fields = ("candidate_name", "email", "job_id")
    readonly_fields = ("id", "created_at")
