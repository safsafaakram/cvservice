from django.db import migrations, models


def populate_cv_ids(apps, schema_editor):
    CV = apps.get_model("cv_app", "CV")
    for index, cv in enumerate(CV.objects.order_by("created_at", "id"), start=1):
        cv.cv_id = index
        cv.save(update_fields=["cv_id"])


class Migration(migrations.Migration):
    dependencies = [
        ("cv_app", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="cv",
            name="cv_id",
            field=models.PositiveIntegerField(
                db_index=True,
                editable=False,
                null=True,
                unique=True,
            ),
        ),
        migrations.RunPython(populate_cv_ids, migrations.RunPython.noop),
    ]
