from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

User = get_user_model()

class EmailOrUsernameBackend(ModelBackend):
    """
    Custom authentication backend that allows users to log in using either
    their username or their email address.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            return None
            
        try:
            # Allow case-insensitive login by username or email
            user = User.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
        except User.DoesNotExist:
            return None
        except User.MultipleObjectsReturned:
            # Fallback if multiple accounts somehow share the same email
            user = User.objects.filter(Q(username__iexact=username) | Q(email__iexact=username)).first()
            
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
