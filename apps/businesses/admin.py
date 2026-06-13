from django.contrib import admin
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

from unfold.admin import ModelAdmin, TabularInline
from .models import Business, OnboardingLink, FAQ, RegistrationRequest
from apps.accounts.models import User
from django.utils.html import format_html
from django.contrib import messages

class FAQInline(TabularInline):
    model = FAQ
    extra = 1
    tab = False

@admin.register(RegistrationRequest)
class RegistrationRequestAdmin(ModelAdmin):
    list_display = ('business_name', 'username', 'email', 'status', 'created_at')
    list_filter = ('status',)
    actions = ['approve_requests_action']

    def process_approval(self, request, reg_request):
        """Helper method to handle the actual approval logic."""
        if User.objects.filter(username=reg_request.username).exists():
            return False, "Username already exists."
        
        try:
            user = User.objects.create_user(
                username=reg_request.username,
                password=reg_request.password,
                email=reg_request.email,
                role=User.Role.BUSINESS_OWNER,
                phone_number=reg_request.phone_number,
                is_staff=True
            )

            Business.objects.create(
                owner=user,
                name=reg_request.business_name,
                email=reg_request.email,
                contact_number=reg_request.phone_number,
                website_url=reg_request.website_url,
                is_setup_complete=False
            )

            from django.contrib.contenttypes.models import ContentType
            from django.contrib.auth.models import Permission
            models_to_grant = [
                ('businesses', 'business'), ('businesses', 'faq'),
                ('assistants', 'assistant'), ('assistants', 'lead'), ('assistants', 'booking'),
            ]
            for app, model in models_to_grant:
                ct = ContentType.objects.get(app_label=app, model=model)
                perms = Permission.objects.filter(content_type=ct, codename__in=[f'view_{model}', f'change_{model}', f'add_{model}'])
                user.user_permissions.add(*perms)

            subject = f"Welcome to NexFlow AI - {reg_request.business_name}"
            email_body = f"""
            Hi {reg_request.username},

            Your business registration for '{reg_request.business_name}' has been APPROVED!

            You can now log in to your Sub-Admin Panel to complete your setup.

            Login URL: {request.build_absolute_uri('/admin/')}
            Username: {reg_request.username}
            Password: (The password you chose during registration)

            Next Steps:
            1. Log in to the admin panel.
            2. Go to 'Businesses' and click on your business name.
            3. Fill out all the required information (Services, Hours, FAQs, etc.).
            4. Save your changes to train your AI Assistant.

            Welcome aboard!
            The NexFlow AI Team
            """
            
            send_mail(subject, email_body, settings.DEFAULT_FROM_EMAIL, [reg_request.email], fail_silently=False)
            return True, "Success"

        except Exception as e:
            logger.error(f"Approval Error: {str(e)}")
            return False, str(e)

    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data and obj.status == RegistrationRequest.Status.APPROVED:
            success, message = self.process_approval(request, obj)
            if success:
                self.message_user(request, f"Account created and email sent to {obj.email}")
            else:
                self.message_user(request, f"Approval logic failed: {message}", messages.ERROR)
        
        super().save_model(request, obj, form, change)

    def approve_requests_action(self, request, queryset):
        count = 0
        for reg_request in queryset.filter(status=RegistrationRequest.Status.PENDING):
            success, message = self.process_approval(request, reg_request)
            if success:
                reg_request.status = RegistrationRequest.Status.APPROVED
                reg_request.save()
                count += 1
            else:
                self.message_user(request, f"Failed to approve {reg_request.username}: {message}", messages.ERROR)
        
        self.message_user(request, f"Successfully approved {count} requests.")

    approve_requests_action.short_description = "Approve and Create Accounts"

@admin.register(Business)
class BusinessAdmin(ModelAdmin):
    list_display = ('name_display', 'owner', 'email', 'is_setup_complete', 'created_at')
    search_fields = ('name', 'email', 'owner__username')
    inlines = [FAQInline]
    
    def name_display(self, obj):
        if obj.name:
            return obj.name
        return format_html('<span style="color: red;">Setup Pending</span>')
    name_display.short_description = "Business Name"

    def public_assistant_link(self, obj):
        if hasattr(obj, 'assistant') and obj.assistant.slug:
            url = f"http://127.0.0.1:8000/assistant/{obj.assistant.slug}/"
            return format_html('<a href="{0}" target="_blank">{0}</a>', url)
        return "Not generated yet"
    public_assistant_link.short_description = "Public AI Assistant Link"

    fieldsets = (
        ('Basic Information', {
            'fields': ('owner', 'name', 'public_assistant_link', 'website_url', 'email', 'contact_number', 'address', 'is_setup_complete')
        }),
        ('Service Details', {
            'fields': ('services_offered', 'service_areas', 'business_hours', 'emergency_service_available')
        }),
        ('AI & Assistant Logic', {
            'fields': ('pricing_info', 'appointment_rules', 'lead_qualification_questions', 'special_instructions')
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser or request.user.role == User.Role.ADMIN:
            return ['public_assistant_link']
        return ['owner', 'is_setup_complete', 'public_assistant_link']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.role == User.Role.ADMIN:
            return qs
        return qs.filter(owner=request.user)

    def has_add_permission(self, request):
        return request.user.is_superuser or request.user.role == User.Role.ADMIN

@admin.register(OnboardingLink)
class OnboardingLinkAdmin(ModelAdmin):
    list_display = ('business_name', 'setup_url', 'is_used', 'created_by', 'created_at')
    readonly_fields = ('token', 'setup_url', 'created_by', 'is_used')
    
    def setup_url(self, obj):
        return f"http://127.0.0.1:8000/api/v1/businesses/links/register_business/?token={obj.token}"
    setup_url.short_description = "Onboarding Link URL"

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def has_module_permission(self, request):
        if not request.user.is_authenticated:
            return False
        return request.user.is_superuser or request.user.role == User.Role.ADMIN
