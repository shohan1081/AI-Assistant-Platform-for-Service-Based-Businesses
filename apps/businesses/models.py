from django.db import models
from django.conf import settings
import uuid

class RegistrationRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    password = models.CharField(max_length=128) # Store temporarily or ask them to set it? Let's capture it as requested.
    
    business_name = models.CharField(max_length=255)
    business_description = models.TextField(help_text="Tell us about your business to get approved")
    website_url = models.URLField(blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Request from {self.business_name} ({self.status})"

class Business(models.Model):
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='business'
    )
    name = models.CharField(max_length=255, blank=True)
    website_url = models.URLField(blank=True, null=True)
    contact_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    service_areas = models.TextField(blank=True, help_text="Comma separated areas")
    services_offered = models.TextField(blank=True, help_text="Comma separated services")
    business_hours = models.JSONField(
        default=dict, 
        blank=True,
        help_text='Format: {"Monday": "9am-5pm", "Saturday": "Closed"}'
    )
    pricing_info = models.TextField(blank=True, null=True)
    appointment_rules = models.TextField(
        blank=True, 
        null=True,
        help_text='e.g., "Must book 24h in advance", "Free cancellations up to 5h before"'
    )
    emergency_service_available = models.BooleanField(default=False)
    lead_qualification_questions = models.TextField(
        blank=True, 
        null=True,
        help_text='e.g., "Are you the homeowner?", "How old is the current roof?"'
    )
    special_instructions = models.TextField(
        blank=True, 
        null=True,
        help_text='Directives for the AI: e.g., "Always be cheerful", "Never give exact dates"'
    )
    ui_theme_color = models.CharField(
        max_length=10, 
        default='#4f46e5', 
        help_text='Hex color code for the chat header and buttons.'
    )
    ui_border_radius = models.CharField(
        max_length=10, 
        default='12px', 
        help_text='e.g., 12px, 0px, 1rem'
    )
    is_setup_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name if self.name else f"Pending Setup ({self.owner.username})"

class FAQ(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='faqs')
    question = models.CharField(max_length=500)
    answer = models.TextField()

    def __str__(self):
        return self.question

class OnboardingLink(models.Model):
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business_name = models.CharField(max_length=255)
    is_used = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_links'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Link for {self.business_name} ({'Used' if self.is_used else 'Available'})"
