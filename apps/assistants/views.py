from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Assistant, Lead, Booking, ChatMessage
from .serializers import AssistantSerializer, LeadSerializer, BookingSerializer, ChatMessageSerializer
from apps.accounts.models import User
from django.conf import settings
from openai import OpenAI
import logging
import re
from django.utils import timezone
from datetime import datetime

logger = logging.getLogger(__name__)

def parse_tag_data(tag_content, keys):
    data = {}
    lookahead = "|".join([f"{k}:" for k in keys])
    for key in keys:
        pattern = rf"{key}:\s*(.*?)\s*(?=(?:{lookahead})|$)"
        match = re.search(pattern, tag_content, re.IGNORECASE)
        if match:
            val = match.group(1).strip()
            if val.endswith(','):
                val = val[:-1].strip()
            data[key.lower()] = val
        else:
            data[key.lower()] = None
    return data


class AssistantViewSet(viewsets.ModelViewSet):
    serializer_class = AssistantSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'slug'

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.ADMIN:
            return Assistant.objects.all()
        return Assistant.objects.filter(business__owner=user)

    @action(detail=False, methods=['get'], url_path='(?P<slug>[^/.]+)/history')
    def history(self, request, slug=None):
        try:
            # We must use the slug from the URL regex named group
            assistant = Assistant.objects.get(slug=slug, is_active=True)
            session_id = request.query_params.get('session_id')
            
            if not session_id:
                return Response({'error': 'session_id is required'}, status=status.HTTP_400_BAD_REQUEST)

            # Retrieve all messages for this session, ordered by time
            messages = ChatMessage.objects.filter(
                assistant=assistant,
                session_id=session_id
            ).order_by('created_at')

            serializer = ChatMessageSerializer(messages, many=True)
            return Response(serializer.data)

        except Assistant.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def get_permissions(self):
        if self.action in ['retrieve_public', 'chat', 'history']:
            return [permissions.AllowAny()]
        return super().get_permissions()

    @action(detail=False, methods=['get'], url_path='(?P<slug>[^/.]+)')
    def retrieve_public(self, request, slug=None):
        try:
            assistant = Assistant.objects.get(slug=slug, is_active=True)
            serializer = self.get_serializer(assistant)
            return Response(serializer.data)
        except Assistant.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'], url_path='(?P<slug>[^/.]+)/chat')
    def chat(self, request, slug=None):
        try:
            assistant = Assistant.objects.get(slug=slug, is_active=True)
            user_message = request.data.get('message')
            session_id = request.data.get('session_id', 'anonymous_session')
            
            if not user_message:
                return Response({'error': 'Message is required'}, status=status.HTTP_400_BAD_REQUEST)

            if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == 'your-openai-api-key-here':
                return Response({'error': 'AI Service not configured'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            # System prompt with business knowledge, lead capture, and booking instructions
            system_prompt = f"""
            You are a professional, friendly, and helpful AI Assistant ONLY for {assistant.business.name}.
            
            GOALS:
            1. Help the customer by answering their questions using ONLY the KNOWLEDGE BASE provided below.
            2. If they want to book or schedule an appointment, collect their booking details (Name, Phone, Email, Service Type, Preferred Date and Time, Location, Notes/details).
            3. Otherwise, naturally collect their contact info (Name, Phone, Service needed) as a lead so a human expert can follow up.
            
            KNOWLEDGE BASE:
            {assistant.knowledge_base}
            
            CRITICAL BOUNDARY RULES:
            1. YOU MUST NEVER ANSWER QUESTIONS OUTSIDE THE SCOPE OF {assistant.business.name}'s BUSINESS AND THE KNOWLEDGE BASE.
            2. If a user asks about general knowledge, politics, weather, other companies, coding, or anything unrelated to the services offered, you must politely decline to answer.
            3. Use a polite deflection that brings the conversation back to the business. 
               Example of how to handle off-topic questions: "I'm here to help you with anything related to the services offered by {assistant.business.name}! If you have questions about our services, pricing, or want to book an appointment, just let me know. How can I assist you today?"
            
            GUIDELINES:
            1. Be very polite. Do NOT be pushy.
            2. If the user asks a specific related question, answer it first using the KNOWLEDGE BASE.
            3. If they want to book an appointment:
               - Ask for and confirm their preferred date and time (convert relative times like "tomorrow at 2pm" to absolute YYYY-MM-DD HH:MM format).
               - Ask for location/address where the service is needed.
               - Ask for their email and any notes about the issue.
               - Ensure you also have their Name and Phone number.
            4. Once you have all the booking details:
               - Thank them by name.
               - Confirm that their appointment request for [Service] on [DateTime] has been received.
               - Mention that a team member will review it and contact them shortly at [Phone Number] to finalize.
               - Provide the business contact number ({assistant.business.contact_number}) if they have urgent questions.
               - Format your response to include this hidden tag at the very end:
                 [BOOKING_DATA: Name: Customer Name, Phone: Phone Number, Email: Email Address, Service: Service Type, DateTime: YYYY-MM-DD HH:MM, Location: Location Address, Notes: Issue Notes]
            5. If they just want a callback or a quote without booking a specific time, format your response to include this hidden tag at the very end:
               [LEAD_DATA: Name: User Name, Phone: User Phone, Service: Service Interest]
            """

            # Retrieve conversation history (last 15 messages from last 16 hours)
            time_threshold = timezone.now() - timezone.timedelta(hours=16)
            history = ChatMessage.objects.filter(
                assistant=assistant,
                session_id=session_id,
                created_at__gte=time_threshold
            ).order_by('created_at')[:15]

            messages = [{"role": "system", "content": system_prompt}]
            for msg in history:
                messages.append({"role": msg.role, "content": msg.content})
            
            messages.append({"role": "user", "content": user_message})

            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages
            )

            ai_response = response.choices[0].message.content
            
            # Save user message and AI response to history
            ChatMessage.objects.create(assistant=assistant, session_id=session_id, role='user', content=user_message)
            ChatMessage.objects.create(assistant=assistant, session_id=session_id, role='assistant', content=ai_response)

            # Extract booking data if AI found it
            if "[BOOKING_DATA:" in ai_response:
                try:
                    booking_part = re.search(r"\[BOOKING_DATA: (.*?)\]", ai_response).group(1)
                    ai_response = re.sub(r"\[BOOKING_DATA: .*?\]", "", ai_response).strip()
                    
                    booking_info = parse_tag_data(booking_part, ["Name", "Phone", "Email", "Service", "DateTime", "Location", "Notes"])
                    
                    date_str = booking_info.get("datetime")
                    preferred_dt = None
                    if date_str:
                        try:
                            clean_date_str = re.search(r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}", date_str)
                            if clean_date_str:
                                dt = datetime.strptime(clean_date_str.group(0), "%Y-%m-%d %H:%M")
                            else:
                                dt = datetime.strptime(date_str, "%Y-%m-%d")
                            preferred_dt = timezone.make_aware(dt)
                        except Exception as dt_err:
                            logger.error(f"Error parsing booking datetime '{date_str}': {str(dt_err)}")
                    
                    if not preferred_dt:
                        preferred_dt = timezone.now() + timezone.timedelta(days=1)
                        
                    Booking.objects.create(
                        business=assistant.business,
                        customer_name=booking_info.get("name") or "Unknown Customer",
                        phone_number=booking_info.get("phone") or "Unknown Phone",
                        email=booking_info.get("email"),
                        service_type=booking_info.get("service") or "General Appointment",
                        preferred_datetime=preferred_dt,
                        location=booking_info.get("location") or "N/A",
                        notes=booking_info.get("notes") or f"Automatically booked via AI Chat. User query: {user_message}"
                    )
                except Exception as e:
                    logger.error(f"Booking Extraction Error: {str(e)}")

            elif "[LEAD_DATA:" in ai_response:
                try:
                    lead_part = re.search(r"\[LEAD_DATA: (.*?)\]", ai_response).group(1)
                    ai_response = re.sub(r"\[LEAD_DATA: .*?\]", "", ai_response).strip()
                    
                    lead_info = parse_tag_data(lead_part, ["Name", "Phone", "Service"])
                    
                    phone = lead_info.get("phone")
                    if phone and phone != "Unknown":
                        Lead.objects.create(
                            business=assistant.business,
                            name=lead_info.get("name") or "Unknown",
                            phone_number=phone.strip(),
                            service_needed=lead_info.get("service") or user_message,
                            message=f"Captured during AI Chat: {user_message}"
                        )
                except Exception as e:
                    logger.error(f"Lead Extraction Error: {str(e)}")

            return Response({'response': ai_response, 'session_id': session_id})

        except Assistant.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"AI Chat Error: {str(e)}")
            return Response({'error': 'Failed to get AI response'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LeadViewSet(viewsets.ModelViewSet):
    serializer_class = LeadSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.role == User.Role.ADMIN:
                return Lead.objects.all()
            return Lead.objects.filter(business__owner=user)
        return Lead.objects.none()

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.role == User.Role.ADMIN:
                return Booking.objects.all()
            return Booking.objects.filter(business__owner=user)
        return Booking.objects.none()

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]
