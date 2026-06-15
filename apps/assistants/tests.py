from django.test import TestCase
from django.core import mail
from django.utils import timezone
from datetime import datetime
from apps.accounts.models import User
from apps.businesses.models import Business
from apps.assistants.models import Booking
from apps.assistants.views import parse_tag_data

class BookingNotificationTestCase(TestCase):
    def setUp(self):
        # Create a business owner
        self.owner = User.objects.create_user(
            username="test_owner",
            password="testpassword",
            email="owner@example.com",
            role=User.Role.BUSINESS_OWNER
        )
        
        # Create a business
        self.business = Business.objects.create(
            owner=self.owner,
            name="Test Services Ltd",
            email="business@example.com",
            contact_number="1234567890",
            website_url="https://testservices.com"
        )

    def test_booking_creates_email_notification(self):
        # Clear the outbox before test
        mail.outbox = []

        preferred_time = timezone.make_aware(datetime(2026, 6, 20, 14, 30))

        # Create a booking
        booking = Booking.objects.create(
            business=self.business,
            customer_name="John Customer",
            phone_number="555-0199",
            email="john@customer.com",
            service_type="Plumbing Repair",
            preferred_datetime=preferred_time,
            location="123 Customer Lane",
            notes="Water pipe leaking in the basement."
        )

        # Verify email is sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]

        # Verify recipients (both business email and owner email)
        self.assertIn("business@example.com", email.to)
        self.assertIn("owner@example.com", email.to)

        # Verify subject
        self.assertEqual(email.subject, "New Booking Request - Test Services Ltd")

        # Verify body content
        self.assertIn("John Customer", email.body)
        self.assertIn("555-0199", email.body)
        self.assertIn("john@customer.com", email.body)
        self.assertIn("Plumbing Repair", email.body)
        self.assertIn("2026-06-20 14:30", email.body)
        self.assertIn("123 Customer Lane", email.body)
        self.assertIn("Water pipe leaking in the basement.", email.body)
        self.assertIn(f"/admin/assistants/booking/{booking.pk}/change/", email.body)


class TagParsingTestCase(TestCase):
    def test_parse_tag_data_perfect_match(self):
        tag_content = "Name: John Doe, Phone: 12345, Email: john@example.com, Service: Root Canal, DateTime: 2026-06-15 10:00, Location: Clinic, Notes: Urgent"
        keys = ["Name", "Phone", "Email", "Service", "DateTime", "Location", "Notes"]
        
        parsed = parse_tag_data(tag_content, keys)
        
        self.assertEqual(parsed["name"], "John Doe")
        self.assertEqual(parsed["phone"], "12345")
        self.assertEqual(parsed["email"], "john@example.com")
        self.assertEqual(parsed["service"], "Root Canal")
        self.assertEqual(parsed["datetime"], "2026-06-15 10:00")
        self.assertEqual(parsed["location"], "Clinic")
        self.assertEqual(parsed["notes"], "Urgent")

    def test_parse_tag_data_missing_fields_and_different_order(self):
        tag_content = "Phone: 555-1234, Name: Alice Smith, Location: Seattle, Notes: Call before arriving"
        keys = ["Name", "Phone", "Email", "Service", "DateTime", "Location", "Notes"]
        
        parsed = parse_tag_data(tag_content, keys)
        
        self.assertEqual(parsed["name"], "Alice Smith")
        self.assertEqual(parsed["phone"], "555-1234")
        self.assertIsNone(parsed["email"])
        self.assertIsNone(parsed["service"])
        self.assertIsNone(parsed["datetime"])
        self.assertEqual(parsed["location"], "Seattle")
        self.assertEqual(parsed["notes"], "Call before arriving")

    def test_parse_tag_data_no_commas(self):
        tag_content = "Name: Bob Phone: 98765 Service: Roof Inspection"
        keys = ["Name", "Phone", "Service"]
        
        parsed = parse_tag_data(tag_content, keys)
        
        self.assertEqual(parsed["name"], "Bob")
        self.assertEqual(parsed["phone"], "98765")
        self.assertEqual(parsed["service"], "Roof Inspection")

