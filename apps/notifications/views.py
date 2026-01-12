from django.shortcuts import render

# Create your views here.


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Notification
from .utils import paginate_queryset

class UserNotificationsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    CATEGORY_MAP = {
        # doctor_appointment, dental_appointment, eye_appointment
        "consultation": [
            "doctor_appointment",
            "dental_appointment",
            "eye_appointment",
        ],

        # pharmacy order
        "pharmacy": [
            "pharmacy_order",  
        ],

        # labtest, sponsored package, health package
        "diagnostic_lab": [
            "lab_appointment",          
            "health_package",
            "sponsored_package",
        ],

        # care_programs
        "care_programs": [
            "care_program",     
        ],

       
    }

    def get(self, request):
        qs = Notification.objects.filter(user=request.user).order_by('-created_at')

        filter_name = request.query_params.get("filter" , "all")

        page= int(request.query_params.get("page" , 1))
        page_size = int(request.query_params.get("page_size" , 10))

        if filter_name != "all":
            item_types = self.CATEGORY_MAP.get(filter_name)
            if item_types is None:
                return Response(
                    {
                        "error":"Invalid filter !"
                    },
                    status=400,
                )
            
            qs= qs.filter(item_type__in=item_types)

        unread = qs.filter(is_read=False).count()


        # PAGINATION

        pagination = paginate_queryset(qs , request)
        paginated_qs= pagination ["results"]

        data = [{
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "is_read": n.is_read,
            "item_type": n.item_type,
            "created_at": n.created_at.strftime("%d/%m/%Y %H:%M")
        } for n in paginated_qs]

        return Response({"filter": filter_name,
                         "unread": unread,
                         "page":pagination["page"], 
                         "page_size": pagination["page_size"] ,
                         
                         "total_pages":pagination["total_pages"],
                         "notifications": data})


class MarkNotificationReadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        n = Notification.objects.get(id=pk, user=request.user)
        n.is_read = True
        n.save()
        return Response({"message": "Marked as read"})



class MarkAllNotificationsReadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # Mark all unread notifications as read
        updated_count = Notification.objects.filter(
            user=user,
            is_read=False
        ).update(is_read=True)

        return Response({
            "message": "All notifications marked as read",
            "updated_count": updated_count
        }, status=200)
