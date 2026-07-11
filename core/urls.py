from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API Schema
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Optional UI:
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Apps
    path('api/v1/accounts/', include('apps.accounts.urls')),
    path('api/v1/businesses/', include('apps.businesses.urls')),
    path('api/v1/assistants/', include('apps.assistants.urls')),
]

from apps.assistants.views import AssistantViewSet
from apps.businesses.views import RegistrationRequestViewSet

# Proxy Compatibility URLs (for frontend client support)
urlpatterns += [
    path('api/proxy/chatbot/<str:slug>/', AssistantViewSet.as_view({'get': 'retrieve_public'}), name='proxy-assistant-public-slash'),
    path('api/proxy/chatbot/<str:slug>', AssistantViewSet.as_view({'get': 'retrieve_public'}), name='proxy-assistant-public'),
    
    path('api/proxy/chatbot/<str:slug>/chat/', AssistantViewSet.as_view({'post': 'chat'}), name='proxy-assistant-chat-slash'),
    path('api/proxy/chatbot/<str:slug>/chat', AssistantViewSet.as_view({'post': 'chat'}), name='proxy-assistant-chat'),
    
    path('api/proxy/chatbot/<str:slug>/history/', AssistantViewSet.as_view({'get': 'history'}), name='proxy-assistant-history-slash'),
    path('api/proxy/chatbot/<str:slug>/history', AssistantViewSet.as_view({'get': 'history'}), name='proxy-assistant-history'),
    
    path('api/proxy/businesses/requests/', RegistrationRequestViewSet.as_view({'post': 'create', 'get': 'list'}), name='proxy-business-requests-slash'),
    path('api/proxy/businesses/requests', RegistrationRequestViewSet.as_view({'post': 'create', 'get': 'list'}), name='proxy-business-requests'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
