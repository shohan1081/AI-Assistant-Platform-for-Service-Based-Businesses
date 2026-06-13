from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify
from .models import Business
from apps.assistants.models import Assistant

@receiver(post_save, sender=Business)
def manage_assistant(sender, instance, created, **kwargs):
    # Compile knowledge for the AI
    kb = f"### BUSINESS PROFILE: {instance.name} ###\n"
    kb += f"Website: {instance.website_url or 'N/A'}\n"
    kb += f"Contact: {instance.contact_number}, Email: {instance.email}\n"
    kb += f"Address: {instance.address}\n"
    kb += f"Service Areas: {instance.service_areas}\n"
    kb += f"Services Offered: {instance.services_offered}\n"
    kb += f"Business Hours: {instance.business_hours}\n"
    kb += f"Emergency Service: {'Available' if instance.emergency_service_available else 'Not Available'}\n"
    kb += f"\n### PRICING & RULES ###\n"
    kb += f"Pricing: {instance.pricing_info or 'Ask for quote'}\n"
    kb += f"Appointment Rules: {instance.appointment_rules or 'N/A'}\n"
    kb += f"Lead Qualification: {instance.lead_qualification_questions or 'N/A'}\n"
    kb += f"\n### FAQS ###\n"
    for faq in instance.faqs.all():
        kb += f"Q: {faq.question}\nA: {faq.answer}\n"
    kb += f"\n### SPECIAL INSTRUCTIONS ###\n"
    kb += f"{instance.special_instructions or 'Respond professionally.'}"

    if created:
        Assistant.objects.create(
            business=instance,
            slug=slugify(instance.name) if instance.name else slugify(instance.owner.username),
            knowledge_base=kb
        )
    else:
        # Update existing assistant whenever business info is updated
        assistant, _ = Assistant.objects.get_or_create(business=instance)
        assistant.knowledge_base = kb
        # Also update slug if name was just fulfilled
        if instance.name and not assistant.slug:
            assistant.slug = slugify(instance.name)
        assistant.save()

    # Automatically check if setup is complete
    required_fields = [
        instance.name, instance.website_url, instance.contact_number,
        instance.email, instance.address, instance.service_areas,
        instance.services_offered, instance.business_hours,
        instance.pricing_info, instance.appointment_rules,
        instance.lead_qualification_questions, instance.special_instructions
    ]
    
    # Check if all fields have values and there is at least one FAQ
    all_fields_filled = all(required_fields)
    has_faqs = instance.faqs.exists()
    
    is_complete = all_fields_filled and has_faqs
    
    if instance.is_setup_complete != is_complete:
        # Use update to avoid re-triggering the signal recursively
        Business.objects.filter(pk=instance.pk).update(is_setup_complete=is_complete)
