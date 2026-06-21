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

