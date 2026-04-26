# Generated for the CV Service microservice.

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CV",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("candidate_name", models.CharField(max_length=255)),
                ("email", models.EmailField(max_length=254)),
                ("file", models.FileField(upload_to="cvs/")),
                ("extracted_text", models.TextField(blank=True)),
                ("score", models.FloatField(blank=True, null=True)),
                ("job_id", models.CharField(db_index=True, max_length=100)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="cv",
            index=models.Index(fields=["job_id", "-score"], name="cv_job_score_idx"),
        ),
    ]
