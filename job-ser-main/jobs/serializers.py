from rest_framework import serializers

from .models import Job


class JobSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source="job_name")
    company = serializers.CharField(required=False, allow_blank=True, default="")
    location = serializers.CharField(required=False, allow_blank=True, default="")
    salary = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Job
        fields = [
            "id",
            "title",
            "description",
            "company",
            "location",
            "salary",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
