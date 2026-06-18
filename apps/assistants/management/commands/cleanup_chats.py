from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.assistants.models import ChatMessage
import datetime

class Command(BaseCommand):
    help = 'Deletes chat messages older than 1 minute to save storage (TESTING ONLY).'

    def handle(self, *args, **options):
        # Calculate the cutoff time (1 minute ago)
        cutoff = timezone.now() - datetime.timedelta(minutes=1)
        
        # Count messages to be deleted
        count = ChatMessage.objects.filter(created_at__lt=cutoff).count()
        
        # Delete them
        ChatMessage.objects.filter(created_at__lt=cutoff).delete()
        
        self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} old chat messages.'))
