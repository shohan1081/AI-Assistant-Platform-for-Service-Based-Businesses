from django.db import models
from apps.businesses.models import Business
import uuid

class Assistant(models.Model):
    business = models.OneToOneField(
        Business,
        on_delete=models.CASCADE,
        related_name='assistant'
    )
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)
    knowledge_base = models.TextField(help_text="Compiled knowledge for the AI")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Assistant for {self.business.name}"

class Lead(models.Model):
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name='leads'
    )
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    service_needed = models.TextField()
    location = models.CharField(max_length=255)
    urgency_level = models.CharField(max_length=50, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Lead: {self.name} for {self.business.name}"

class Booking(models.Model):
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    customer_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    service_type = models.CharField(max_length=255)
    preferred_datetime = models.DateTimeField()
    location = models.CharField(max_length=255)
    notes = models.TextField(blank=True, null=True)
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('CONFIRMED', 'Confirmed'),
            ('CANCELLED', 'Cancelled'),
        ],
        default='PENDING'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking: {self.customer_name} on {self.preferred_datetime}"

class ChatMessage(models.Model):
    assistant = models.ForeignKey(Assistant, on_delete=models.CASCADE, related_name='chat_messages')
    session_id = models.CharField(max_length=255, db_index=True)
    role = models.CharField(max_length=20, choices=[('user', 'User'), ('assistant', 'Assistant')])
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role} in {self.session_id} - {self.assistant.business.name}"
