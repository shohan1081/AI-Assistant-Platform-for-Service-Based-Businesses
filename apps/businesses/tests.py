from django.test import TestCase
from rest_framework.exceptions import ValidationError
from apps.businesses.serializers import RegistrationRequestSerializer

class RegistrationRequestSerializerTestCase(TestCase):
    def setUp(self):
        self.base_data = {
            "username": "shohan_test",
            "email": "shohan@example.com",
            "phone_number": "12345678",
            "business_name": "Shohan Services",
            "business_description": "We offer top quality service.",
            "website_url": "https://shohan.com"
        }

    def test_valid_password_passes(self):
        data = self.base_data.copy()
        data["password"] = "SecurePass123!"
        
        serializer = RegistrationRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_password_missing_uppercase_fails(self):
        data = self.base_data.copy()
        data["password"] = "securepass123!"
        
        serializer = RegistrationRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)
        self.assertEqual(serializer.errors["password"][0], "Password must contain at least one uppercase letter.")

    def test_password_missing_number_fails(self):
        data = self.base_data.copy()
        data["password"] = "SecurePass!"
        
        serializer = RegistrationRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)
        self.assertEqual(serializer.errors["password"][0], "Password must contain at least one number.")

    def test_password_missing_special_char_fails(self):
        data = self.base_data.copy()
        data["password"] = "SecurePass123"
        
        serializer = RegistrationRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)
        self.assertEqual(serializer.errors["password"][0], "Password must contain at least one special character.")

    def test_unique_assistant_slug_generation(self):
        from apps.assistants.models import Assistant
        from apps.accounts.models import User
        from apps.businesses.models import Business

        owner1 = User.objects.create_user(
            username="owner1",
            password="SecurePass123!",
            email="owner1@example.com",
            role=User.Role.BUSINESS_OWNER
        )
        owner2 = User.objects.create_user(
            username="owner2",
            password="SecurePass123!",
            email="owner2@example.com",
            role=User.Role.BUSINESS_OWNER
        )

        b1 = Business.objects.create(owner=owner1, name="Elite Pro")
        b2 = Business.objects.create(owner=owner2, name="Elite-Pro")

        a1 = Assistant.objects.get(business=b1)
        a2 = Assistant.objects.get(business=b2)

        self.assertEqual(a1.slug, "elite-pro")
        self.assertEqual(a2.slug, "elite-pro-1")

    def test_duplicate_usernames_allowed_in_requests(self):
        from apps.businesses.models import RegistrationRequest
        
        # Create first request
        data1 = self.base_data.copy()
        data1["username"] = "duplicate_username"
        data1["password"] = "SecurePass123!"
        data1["business_name"] = "Business One"
        
        serializer1 = RegistrationRequestSerializer(data=data1)
        self.assertTrue(serializer1.is_valid())
        serializer1.save()
        
        # Create second request with the same username but different business name
        data2 = self.base_data.copy()
        data2["username"] = "duplicate_username"
        data2["password"] = "SecurePass123!"
        data2["business_name"] = "Business Two"
        
        serializer2 = RegistrationRequestSerializer(data=data2)
        self.assertTrue(serializer2.is_valid())
        serializer2.save()
        
        self.assertEqual(RegistrationRequest.objects.filter(username="duplicate_username").count(), 2)

    def test_duplicate_business_names_rejected_in_requests(self):
        from apps.accounts.models import User
        from apps.businesses.models import Business, RegistrationRequest
        
        # 1. Test collision with existing Business name
        owner = User.objects.create_user(username="owner_temp", password="SecurePass123!", email="temp@test.com", role=User.Role.BUSINESS_OWNER)
        Business.objects.create(owner=owner, name="Existing Shop")
        
        data1 = self.base_data.copy()
        data1["password"] = "SecurePass123!"
        data1["business_name"] = "Existing Shop"
        
        serializer1 = RegistrationRequestSerializer(data=data1)
        self.assertFalse(serializer1.is_valid())
        self.assertIn("business_name", serializer1.errors)
        self.assertEqual(serializer1.errors["business_name"][0], "A business with this name already exists.")
        
        # 2. Test collision with pending RegistrationRequest business_name
        data2 = self.base_data.copy()
        data2["password"] = "SecurePass123!"
        data2["business_name"] = "Pending Shop"
        
        serializer2 = RegistrationRequestSerializer(data=data2)
        self.assertTrue(serializer2.is_valid())
        serializer2.save()
        
        # Try registering with the same business name
        data3 = self.base_data.copy()
        data3["password"] = "SecurePass123!"
        data3["business_name"] = "Pending Shop"
        
        serializer3 = RegistrationRequestSerializer(data=data3)
        self.assertFalse(serializer3.is_valid())
        self.assertIn("business_name", serializer3.errors)
        self.assertEqual(serializer3.errors["business_name"][0], "A registration request for this business name is already pending.")



