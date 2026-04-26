from django.urls import path

from .views import (
    CVInternalScoreUpdateView,
    CVJobRankingView,
    CVUploadView,
    JobRankingDetailView,
)


urlpatterns = [
    path("upload/", CVUploadView.as_view(), name="cv-upload"),
    path("cv/upload/", CVUploadView.as_view(), name="cv-upload-legacy"),
    path("job/<str:job_id>/", JobRankingDetailView.as_view(), name="job-ranking-detail"),
    path("cv/job/<str:job_id>/", CVJobRankingView.as_view(), name="cv-job-ranking"),
    path(
        "internal/cv/<int:cv_id>/score/",
        CVInternalScoreUpdateView.as_view(),
        name="cv-update-score-internal",
    ),
]
