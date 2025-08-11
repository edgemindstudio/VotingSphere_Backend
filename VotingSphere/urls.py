# VotingSphere/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# JWT
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from accounts.serializers import EmailOrUsernameTokenObtainPairSerializer

# OpenAPI docs (drf-spectacular)
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

# ---- Custom token view that accepts email OR username ----
class EmailOrUsernameTokenView(TokenObtainPairView):
    serializer_class = EmailOrUsernameTokenObtainPairSerializer

urlpatterns = [
    path("admin/", admin.site.urls),

    # dj-rest-auth (optional; keep if you use these)
    path("api/auth/", include("dj_rest_auth.urls")),
    path("api/auth/registration/", include("dj_rest_auth.registration.urls")),

    # API schema & docs
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="api-schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="api-schema"), name="redoc"),

    # Auth (JWT)
    path("api/token/", EmailOrUsernameTokenView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # App routes
    path("api/v1/", include("voting.urls")),

    # Browsable API login/logout
    path("api-auth/", include("rest_framework.urls")),
]

if settings.DEBUG:
    if getattr(settings, "MEDIA_URL", None) and getattr(settings, "MEDIA_ROOT", None):
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
