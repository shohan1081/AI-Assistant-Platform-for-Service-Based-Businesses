from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Assistant, Lead, Booking
from apps.accounts.models import User

class BaseBusinessAdmin(ModelAdmin):
    """Base class to filter records by the logged-in business owner using Unfold."""
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.role == User.Role.ADMIN:
            return qs
        if hasattr(self.model, 'business'):
            return qs.filter(business__owner=request.user)
        return qs

    def has_change_permission(self, request, obj=None):
        if obj is not None and not request.user.is_superuser and request.user.role != User.Role.ADMIN:
            if hasattr(obj, 'business'):
                return obj.business.owner == request.user
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and not request.user.is_superuser and request.user.role != User.Role.ADMIN:
            if hasattr(obj, 'business'):
                return obj.business.owner == request.user
        return super().has_delete_permission(request, obj)

@admin.register(Assistant)
class AssistantAdmin(BaseBusinessAdmin):
    list_display = ('business', 'slug', 'is_active')
    search_fields = ('slug', 'business__name')

@admin.register(Lead)
class LeadAdmin(BaseBusinessAdmin):
    list_display = ('name', 'business', 'service_needed', 'created_at')
    list_filter = ('business', 'created_at')

    def get_list_filter(self, request):
        if request.user.is_superuser or request.user.role == User.Role.ADMIN:
            return super().get_list_filter(request)
        return ('created_at',)

@admin.register(Booking)
class BookingAdmin(BaseBusinessAdmin):
    list_display = ('customer_name', 'business', 'preferred_datetime', 'status')
    list_filter = ('business', 'status', 'preferred_datetime')

    def get_list_filter(self, request):
        if request.user.is_superuser or request.user.role == User.Role.ADMIN:
            return super().get_list_filter(request)
        return ('status', 'preferred_datetime')
