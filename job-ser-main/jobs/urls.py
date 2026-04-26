from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import InternalJobDetailView, JobViewSet


router = DefaultRouter()
router.register(r"jobs", JobViewSet, basename="jobs")

urlpatterns = [
    path("", include(router.urls)),
    path("internal/jobs/<int:job_id>/", InternalJobDetailView.as_view(), name="internal-job-detail"),
]
