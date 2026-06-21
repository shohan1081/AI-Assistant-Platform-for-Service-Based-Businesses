from rest_framework import serializers
from .models import Business, OnboardingLink

class BusinessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = '__all__'
        read_only_fields = ('owner', 'created_at', 'updated_at')

class OnboardingLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnboardingLink
        fields = '__all__'
        read_only_fields = ('token', 'created_by', 'created_at', 'is_used')

class BusinessRegistrationSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField()
    phone_number = serializers.CharField(required=False)

    def validate_username(self, value):
        from apps.accounts.models import User
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken. Please choose another one.")
        return value

    def validate_token(self, value):
        try:
            link = OnboardingLink.objects.get(token=value, is_used=False)
        except OnboardingLink.DoesNotExist:
            raise serializers.ValidationError("Invalid or already used onboarding token.")
        return value

    def create(self, validated_data):
        from apps.accounts.models import User
        token = validated_data.pop('token')
        link = OnboardingLink.objects.get(token=token)
        
        # Create the user
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data['email'],
            role=User.Role.BUSINESS_OWNER,
            phone_number=validated_data.get('phone_number', ''),
            is_staff=True  # Allow access to Django Admin
        )

        # Create the business profile (the "sub admin panel" data)
        Business.objects.create(
            owner=user,
            name=link.business_name,
            is_setup_complete=False # New field
        )

        # Mark token as used
        link.is_used = True
        link.save()

        # Grant permissions so they can see and edit their data in Django Admin
        from django.contrib.contenttypes.models import ContentType
        from django.contrib.auth.models import Permission
        
        models_to_grant = [
            ('businesses', 'business'),
            ('businesses', 'faq'),
            ('assistants', 'assistant'),
            ('assistants', 'lead'),
            ('assistants', 'booking'),
        ]
        
        for app_label, model_name in models_to_grant:
            content_type = ContentType.objects.get(app_label=app_label, model=model_name)
            permissions = Permission.objects.filter(
                content_type=content_type, 
                codename__in=[f'view_{model_name}', f'change_{model_name}', f'add_{model_name}']
            )
            user.user_permissions.add(*permissions)

        return user

from .models import RegistrationRequest

class RegistrationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistrationRequest
        fields = ('username', 'password', 'email', 'phone_number', 'business_name', 'business_description', 'website_url')
        extra_kwargs = {'password': {'write_only': True}}

    def validate_password(self, value):
        if not any(char.isupper() for char in value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter.")
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError("Password must contain at least one number.")
        if not any(not char.isalnum() and not char.isspace() for char in value):
            raise serializers.ValidationError("Password must contain at least one special character.")
        return value

    def validate_business_name(self, value):
        from .models import Business
        if Business.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("A business with this name already exists.")
        if RegistrationRequest.objects.filter(business_name__iexact=value, status=RegistrationRequest.Status.PENDING).exists():
            raise serializers.ValidationError("A registration request for this business name is already pending.")
        return value


