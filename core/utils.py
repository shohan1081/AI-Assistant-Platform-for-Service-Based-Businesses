from django.db.models import Count, functions
from django.utils import timezone
from datetime import timedelta

def get_site_header(request):
    if hasattr(request, 'user') and request.user.is_authenticated:
        if getattr(request.user, 'role', None) == 'BUSINESS_OWNER':
            if hasattr(request.user, 'business') and request.user.business.name:
                return request.user.business.name
    return "NexSell Connect Admin"

def get_site_title(request):
    return get_site_header(request)

def get_site_index_title(request):
    return "Dashboard"

def dashboard_callback(request, context):
    """
    Callback to inject dynamic analytics data into the Unfold admin dashboard.
    """
    if not request.user.is_authenticated or request.user.role != 'BUSINESS_OWNER':
        return context

    # Import models here to avoid AppRegistryNotReady error
    from apps.assistants.models import ChatMessage, Lead, Booking

    business = request.user.business
    today = timezone.now().date()
    last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    
    # 1. Client Queries per day (Last 7 Days)
    queries_data = ChatMessage.objects.filter(
        assistant__business=business,
        role='user',
        created_at__date__gte=last_7_days[0]
    ).annotate(date=functions.TruncDate('created_at')).values('date').annotate(count=Count('id')).order_by('date')
    
    query_counts = {q['date']: q['count'] for q in queries_data}
    queries_chart = {
        "labels": [d.strftime("%b %d") for d in last_7_days],
        "datasets": [{
            "label": "User Queries",
            "data": [query_counts.get(d, 0) for d in last_7_days],
            "backgroundColor": "#4f46e5",
            "borderColor": "#4f46e5",
        }]
    }

    # 2. Popular Service Types (From Bookings)
    services_data = Booking.objects.filter(business=business).values('service_type').annotate(count=Count('id')).order_by('-count')[:5]
    services_chart = {
        "labels": [s['service_type'] for s in services_data],
        "datasets": [{
            "label": "Bookings per Service",
            "data": [s['count'] for s in services_data],
            "backgroundColor": ["#6366f1", "#8b5cf6", "#a855f7", "#d946ef", "#ec4899"],
        }]
    }

    # 3. Most Client Areas (From Leads/Bookings)
    areas_data = Lead.objects.filter(business=business).values('location').annotate(count=Count('id')).order_by('-count')[:5]
    areas_chart = {
        "labels": [a['location'] or "Unknown" for a in areas_data],
        "datasets": [{
            "label": "Leads per Area",
            "data": [a['count'] for a in areas_data],
            "backgroundColor": "#10b981",
        }]
    }

    # 4. KPIs
    context.update({
        "kpi_total_leads": Lead.objects.filter(business=business).count(),
        "kpi_total_bookings": Booking.objects.filter(business=business).count(),
        "kpi_total_conversations": ChatMessage.objects.filter(assistant__business=business).values('session_id').distinct().count(),
        "queries_chart": queries_chart,
        "services_chart": services_chart,
        "areas_chart": areas_chart,
    })
    
    return context
