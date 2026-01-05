from django.urls import path
from .views import ChatSessionAPIView, ChatMessageAPIView

urlpatterns = [
    path('sessions/', ChatSessionAPIView.as_view(), name='chat-sessions'),
    path('sessions/<int:session_id>/messages/', ChatMessageAPIView.as_view(), name='chat-messages'),
]
