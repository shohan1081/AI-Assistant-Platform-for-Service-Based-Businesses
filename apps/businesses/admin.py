from django.contrib import admin
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags, format_html
from django.utils.safestring import mark_safe
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)

from unfold.admin import ModelAdmin, TabularInline
from .models import Business, OnboardingLink, FAQ, RegistrationRequest
from .forms import BusinessAdminForm, DAYS_OF_WEEK
from apps.accounts.models import User

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
            login_url = request.build_absolute_uri('/admin/')
            
            context = {
                'username': reg_request.username,
                'business_name': reg_request.business_name,
                'login_url': login_url,
            }
            
            html_message = render_to_string('emails/approval_welcome.html', context)
            plain_message = strip_tags(html_message)
            
            try:
                send_mail(
                    subject, 
                    plain_message, 
                    settings.DEFAULT_FROM_EMAIL, 
                    [reg_request.email], 
                    html_message=html_message,
                    fail_silently=False
                )
                logger.info(f"Approval email sent successfully to {reg_request.email}")
                return True, "Account created and welcome email sent."
            except Exception as email_error:
                logger.error(f"Email sending failed for {reg_request.email}: {str(email_error)}")
                return True, f"Account created, but welcome email failed to send. Error: {str(email_error)}"

        except Exception as e:
            logger.exception(f"Approval Error for {reg_request.username}: {str(e)}")
            return False, f"System error during approval: {str(e)}"

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
    form = BusinessAdminForm
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

    def embed_code(self, obj):
        if hasattr(obj, 'assistant') and obj.assistant.slug:
            code = f'<!-- Paste this in your website body -->\n<script src="https://nexflow.com/widget.js" data-slug="{obj.assistant.slug}"></script>'
            return format_html('<pre style="background: #f8f9fa; padding: 15px; border-radius: 8px; font-family: monospace; border: 1px solid #e5e7eb;">{}</pre>', code)
        return "Complete setup to generate your embed code."
    embed_code.short_description = "Website Embed Code"

    def setup_progress(self, obj):
        if not obj.pk:
            return "Save the business first to see progress."
            
        required_fields = {
            'Name': obj.name,
            'Website': obj.website_url,
            'Contact Number': obj.contact_number,
            'Email': obj.email,
            'Address': obj.address,
            'Service Areas': obj.service_areas,
            'Services Offered': obj.services_offered,
            'Business Hours': obj.business_hours,
            'Pricing Info': obj.pricing_info,
            'Appointment Rules': obj.appointment_rules,
            'Lead Qual. Questions': obj.lead_qualification_questions,
            'Special Instructions': obj.special_instructions,
        }
        
        missing = [label for label, val in required_fields.items() if not val]
        has_faqs = obj.faqs.exists()
        
        if not missing and has_faqs:
            return mark_safe('<b style="color: green;">✅ Setup Complete! AI Assistant is ready.</b>')
        
        error_msg = '<ul style="color: #d9534f; margin: 0; padding-left: 20px;">'
        for item in missing:
            error_msg += f'<li>Missing: {item}</li>'
        if not has_faqs:
            error_msg += '<li>Missing: At least one FAQ</li>'
        error_msg += '</ul>'
        
        return mark_safe(error_msg)
    setup_progress.short_description = "Setup Status / Missing Info"

    fieldsets = (
        ('Setup Status', {
            'fields': ('setup_progress',),
        }),
        ('Basic Information', {
            'fields': ('owner', 'name', 'public_assistant_link', 'embed_code', 'website_url', 'email', 'contact_number', 'address', 'is_setup_complete', 'business_hours')
        }),
        ('UI Customization', {
            'fields': ('ui_theme_color', 'ui_border_radius')
        }),
        ('Business Hours', {
            'fields': [
                (f'{day}_active', f'{day}_start', f'{day}_end') for day in DAYS_OF_WEEK
            ]
        }),
        ('Service Details', {
            'fields': ('services_offered', 'service_areas', 'emergency_service_available')
        }),
        ('AI & Assistant Logic', {
            'fields': ('pricing_info', 'appointment_rules', 'lead_qualification_questions', 'special_instructions')
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        base_readonly = ['public_assistant_link', 'embed_code', 'setup_progress']
        if request.user.is_superuser or request.user.role == User.Role.ADMIN:
            return base_readonly
        return ['owner', 'is_setup_complete'] + base_readonly

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
