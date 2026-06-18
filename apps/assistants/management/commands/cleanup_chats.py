from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.assistants.models import ChatMessage
import datetime

class Command(BaseCommand):
    help = 'Deletes chat messages older than 10 hours to save storage.'

    def handle(self, *args, **options):
        # Calculate the cutoff time (10 hours ago)
        cutoff = timezone.now() - datetime.timedelta(hours=10)
        
        # Count messages to be deleted
        count = ChatMessage.objects.filter(created_at__lt=cutoff).count()
        
        # Delete them
        ChatMessage.objects.filter(created_at__lt=cutoff).delete()
        
        self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} old chat messages.'))
