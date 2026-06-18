from rest_framework import serializers
from .models import Assistant, Lead, Booking, ChatMessage

class AssistantSerializer(serializers.ModelSerializer):
    business_name = serializers.CharField(source='business.name', read_only=True)
    ui_theme_color = serializers.CharField(source='business.ui_theme_color', read_only=True)
    ui_text_color = serializers.CharField(source='business.ui_text_color', read_only=True)
    ui_border_radius = serializers.CharField(source='business.ui_border_radius', read_only=True)

    class Meta:
        model = Assistant
        fields = ['id', 'slug', 'business_name', 'is_active', 'ui_theme_color', 'ui_text_color', 'ui_border_radius', 'created_at', 'updated_at']
        read_only_fields = ('created_at', 'updated_at')

class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = '__all__'
        read_only_fields = ('created_at',)

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = ('created_at',)

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['role', 'content', 'created_at']
