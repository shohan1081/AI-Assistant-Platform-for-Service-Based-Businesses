import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Booking

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Booking)
def send_booking_notification(sender, instance, created, **kwargs):
    if not created:
        return

    try:
        business = instance.business
        owner = business.owner
        
        # Determine recipient email(s)
        recipients = []
        if business.email:
            recipients.append(business.email)
        if owner.email and owner.email not in recipients:
            recipients.append(owner.email)
            
        if not recipients:
            logger.warning(f"No notification email address found for business '{business.name or business.owner.username}'")
            return
            
        # Format the datetime for readability
        dt_str = instance.preferred_datetime.strftime('%Y-%m-%d %H:%M')
        
        # Build the admin URL to review the booking
        # Since we might not know the exact domain dynamically, we construct a standard dev link.
        # Production setups would configure hostnames accordingly.
        admin_url = f"https://nexsellconnect.com/admin/assistants/booking/{instance.pk}/change/"
        
        subject = f"New Booking Request - {business.name or 'Your Business'}"
        
        email_body = f"""
Hi {owner.username or 'Business Owner'},

A new appointment booking has been scheduled through your AI Assistant page!

Booking Details:
----------------------------------
Customer Name:      {instance.customer_name}
Phone Number:       {instance.phone_number}
Email Address:      {instance.email or 'N/A'}
Service Type:       {instance.service_type}
Preferred Date/Time:{dt_str}
Location:           {instance.location}
Notes:              {instance.notes or 'None'}
----------------------------------

You can review, confirm, or cancel this booking directly from your admin dashboard:
{admin_url}

Best regards,
The NexSell Connect Team
"""

        send_mail(
            subject=subject,
            message=email_body,
            from_email=settings.DEFAULT_FROM_EMAIL or 'noreply@nexsellconnect.com',
            recipient_list=recipients,
            fail_silently=False
        )
        logger.info(f"Successfully sent booking notification email to {recipients} for booking ID {instance.pk}")

    except Exception as e:
        # Wrap everything in a try-except to ensure saving a booking never crashes due to mail failures
        logger.error(f"Failed to send booking notification email for booking {instance.pk}: {str(e)}")
