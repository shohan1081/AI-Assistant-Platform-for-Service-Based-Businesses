from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BusinessViewSet, OnboardingLinkViewSet, RegistrationRequestViewSet

router = DefaultRouter()
router.register(r'profile', BusinessViewSet, basename='business')
router.register(r'links', OnboardingLinkViewSet, basename='onboarding-links')
router.register(r'requests', RegistrationRequestViewSet, basename='registration-requests')

urlpatterns = [
    path('', include(router.urls)),
]
