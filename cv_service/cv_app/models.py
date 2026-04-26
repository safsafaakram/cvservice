import uuid

from django.db import models


class CV(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cv_id = models.PositiveIntegerField(
        unique=True,
        editable=False,
        null=True,
        db_index=True,
    )
    candidate_name = models.CharField(max_length=255)
    email = models.EmailField()
    file = models.FileField(upload_to="cvs/")
    extracted_text = models.TextField(blank=True)
    score = models.FloatField(null=True, blank=True)
    job_id = models.CharField(max_length=100, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["job_id", "-score"], name="cv_job_score_idx"),
        ]

    def __str__(self):
        return f"{self.candidate_name} ({self.job_id})"

    def save(self, *args, **kwargs):
        if self.cv_id is None:
            max_cv_id = CV.objects.aggregate(models.Max("cv_id"))["cv_id__max"] or 0
            self.cv_id = max_cv_id + 1
        super().save(*args, **kwargs)
