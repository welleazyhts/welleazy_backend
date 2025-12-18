from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json


@csrf_exempt
def partner_request(request):
    # Handle 'Partner with us' form and send email.

    if request.method != "POST":
        return JsonResponse(
            {"status": "error", "message": "Invalid request method"},
            status=400,
        )

    try:
        # Parse JSON body
        data = json.loads(request.body)

        name = data.get("name")
        business_type = data.get("business_type")
        phone_number = data.get("phone_number")
        user_email = data.get("email")
        message = data.get("message")

        # Basic validation
        if not (name and phone_number and user_email and message):
            return JsonResponse(
                {
                    "status": "error",
                    "message": "name, phone_number, email, message are required",
                },
                status=400,
            )

        # Email subject & body
        subject = "New Partner Request"
        email_body = f"""
                        New Partner Enquiry

                        Name: {name}
                        Business Type: {business_type}
                        Phone Number: {phone_number}
                        Email: {user_email}
                        Message:{message}
                        """.strip()

        # Email setup
        email_message = EmailMessage(
            subject=subject,
            body=email_body,
            from_email=user_email,   
            to=[settings.EMAIL_HOST_USER],    
            reply_to=[user_email],        
        )

        email_message.send(fail_silently=False)

        return JsonResponse(
            {"status": "success", "message": "Partner request sent successfully!"}
        )

    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": str(e)},
            status=500,
        )
