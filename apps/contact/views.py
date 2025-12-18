from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .serializers import ContactSerializer
from rest_framework.parsers import JSONParser


@csrf_exempt
def submit_contact(request):

    if request.method == "POST":
        try:
            data = JSONParser().parse(request)

            serializer = ContactSerializer(data=data)

            if not serializer.is_valid():
                return JsonResponse(
                    {"status": "error", "message": serializer.errors},
                    status=400
                )

            validated = serializer.validated_data

            full_name     = validated["full_name"]
            company_name  = validated["company_name"]
            phone_number  = validated["phone_number"]
            user_email    = validated["email"]
            message       = validated["message"]

            subject = "New Contact Form Submission"
            email_body = (
                f"Full Name: {full_name}\n"
                f"Company: {company_name}\n"
                f"Phone: {phone_number}\n"
                f"Email: {user_email}\n"
                f"Message: {message}\n"
            )

            email_message = EmailMessage(
                subject=subject,
                body=email_body,
                from_email=user_email,
                to=[settings.EMAIL_HOST_USER],
                reply_to=[user_email], 
            )

            email_message.send(fail_silently=False)

            return JsonResponse({"status": "success", "message": "Email sent successfully!"})

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)
