from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Business, OnboardingLink, RegistrationRequest
from .serializers import BusinessSerializer, OnboardingLinkSerializer, BusinessRegistrationSerializer, RegistrationRequestSerializer
from apps.accounts.models import User


class RegistrationRequestViewSet(viewsets.ModelViewSet):
    queryset = RegistrationRequest.objects.all()
    serializer_class = RegistrationRequestSerializer
    permission_classes = [permissions.AllowAny]

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

class BusinessViewSet(viewsets.ModelViewSet):
    serializer_class = BusinessSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.ADMIN:
            return Business.objects.all()
        return Business.objects.filter(owner=user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class OnboardingLinkViewSet(viewsets.ModelViewSet):
    queryset = OnboardingLink.objects.all()
    serializer_class = OnboardingLinkSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def register_business(self, request):
        # Extract token from URL query parameters if not in body
        data = request.data.copy()
        if 'token' not in data and 'token' in request.query_params:
            data['token'] = request.query_params.get('token')
            
        serializer = BusinessRegistrationSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'Registration successful',
                'user': user.username,
                'business_name': user.business.name
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny], url_path='validate/(?P<token>[^/.]+)')
    def validate_token(self, request, token=None):
        try:
            link = OnboardingLink.objects.get(token=token, is_used=False)
            return Response({'valid': True, 'business_name': link.business_name})
        except OnboardingLink.DoesNotExist:
            return Response({'valid': False}, status=status.HTTP_404_NOT_FOUND)
