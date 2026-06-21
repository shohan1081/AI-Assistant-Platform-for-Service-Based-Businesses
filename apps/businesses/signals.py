from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.text import slugify
from .models import Business, FAQ
from apps.assistants.models import Assistant

def generate_unique_slug(base_name, exclude_assistant_id=None):
    base_slug = slugify(base_name)
    if not base_slug:
        base_slug = "assistant"
        
    slug = base_slug
    counter = 1
    
    query = Assistant.objects.filter(slug=slug)
    if exclude_assistant_id:
        query = query.exclude(pk=exclude_assistant_id)
        
    while query.exists():
        slug = f"{base_slug}-{counter}"
        query = Assistant.objects.filter(slug=slug)
        if exclude_assistant_id:
            query = query.exclude(pk=exclude_assistant_id)
        counter += 1
        
    return slug

def update_business_assistant_and_status(business):
    """Helper function to update assistant KB and business setup status."""
    # Compile knowledge for the AI
    kb = f"### BUSINESS PROFILE: {business.name} ###\n"
    kb += f"Website: {business.website_url or 'N/A'}\n"
    kb += f"Contact: {business.contact_number}, Email: {business.email}\n"
    kb += f"Address: {business.address}\n"
    kb += f"Service Areas: {business.service_areas}\n"
    kb += f"Services Offered: {business.services_offered}\n"
    kb += f"Business Hours: {business.business_hours}\n"
    kb += f"Emergency Service: {'Available' if business.emergency_service_available else 'Not Available'}\n"
    kb += f"\n### PRICING & RULES ###\n"
    kb += f"Pricing: {business.pricing_info or 'Ask for quote'}\n"
    kb += f"Appointment Rules: {business.appointment_rules or 'N/A'}\n"
    kb += f"Lead Qualification: {business.lead_qualification_questions or 'N/A'}\n"
    kb += f"\n### FAQS ###\n"
    for faq in business.faqs.all():
        kb += f"Q: {faq.question}\nA: {faq.answer}\n"
    kb += f"\n### SPECIAL INSTRUCTIONS ###\n"
    kb += f"{business.special_instructions or 'Respond professionally.'}"

    # Update existing assistant whenever business info is updated
    assistant, created = Assistant.objects.get_or_create(business=business)
    assistant.knowledge_base = kb
    # Also update slug if name was just fulfilled
    if business.name and not assistant.slug:
        assistant.slug = generate_unique_slug(business.name, exclude_assistant_id=assistant.pk)
    assistant.save()

    # Automatically check if setup is complete
    required_fields = [
        business.name, business.website_url, business.contact_number,
        business.email, business.address, business.service_areas,
        business.services_offered, business.business_hours,
        business.pricing_info, business.appointment_rules,
        business.lead_qualification_questions, business.special_instructions
    ]
    
    # Check if all fields have values and there is at least one FAQ
    all_fields_filled = all(required_fields)
    has_faqs = business.faqs.exists()
    
    is_complete = all_fields_filled and has_faqs
    
    if business.is_setup_complete != is_complete:
        # Use update to avoid re-triggering the signal recursively
        Business.objects.filter(pk=business.pk).update(is_setup_complete=is_complete)

@receiver(post_save, sender=Business)
def manage_assistant(sender, instance, created, **kwargs):
    if created:
        base_name = instance.name if instance.name else instance.owner.username
        slug = generate_unique_slug(base_name)
        Assistant.objects.create(
            business=instance,
            slug=slug,
            knowledge_base=f"Welcome to {instance.name or instance.owner.username}"
        )
    
    update_business_assistant_and_status(instance)

@receiver([post_save, post_delete], sender=FAQ)
def handle_faq_change(sender, instance, **kwargs):
    """Update business status when FAQs are changed."""
    if instance.business:
        update_business_assistant_and_status(instance.business)
