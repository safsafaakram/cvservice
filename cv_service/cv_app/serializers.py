from rest_framework import serializers

from .models import CV


class CVUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = CV
        fields = ("candidate_name", "email", "job_id", "file")

    def validate_file(self, uploaded_file):
        filename = uploaded_file.name.lower()
        if not filename.endswith(".pdf"):
            raise serializers.ValidationError("Only PDF files are supported.")

        current_position = uploaded_file.tell()
        header = uploaded_file.read(5)
        uploaded_file.seek(current_position)

        if header != b"%PDF-":
            raise serializers.ValidationError("Uploaded file is not a valid PDF.")

        return uploaded_file


class CVSerializer(serializers.ModelSerializer):
    class Meta:
        model = CV
        fields = (
            "cv_id",
            "candidate_name",
            "email",
            "file",
            "job_id",
            "score",
            "created_at",
        )
        read_only_fields = fields
