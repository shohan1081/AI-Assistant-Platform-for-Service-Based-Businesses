from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AssistantViewSet, LeadViewSet, BookingViewSet

router = DefaultRouter()
router.register(r'manage', AssistantViewSet, basename='assistant-manage')
router.register(r'public', AssistantViewSet, basename='assistant-public')
router.register(r'leads', LeadViewSet, basename='leads')
router.register(r'bookings', BookingViewSet, basename='bookings')

urlpatterns = [
    path('', include(router.urls)),
]
