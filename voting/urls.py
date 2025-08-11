# voting/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import ElectionViewSet, CandidateViewSet, VoteViewSet, CategoryViewSet, NotificationViewSet

app_name = "voting"

# Auto-generates CRUD routes like /elections/, /elections/{id}/, etc.
router = DefaultRouter() # shows a browsable root at /api/v1/
router.register(r'elections', ElectionViewSet, basename='election')
router.register(r'candidates', CandidateViewSet, basename='candidate')
router.register(r'votes', VoteViewSet, basename='vote')
router.register(r'categories', CategoryViewSet, basename='category')

urlpatterns = [
    path('', include(router.urls)),  # Includes all the auto-generated routes
]

