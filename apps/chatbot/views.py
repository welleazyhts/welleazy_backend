from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import ChatSession, ChatMessage
from .serializers import ChatSessionSerializer, ChatMessageSerializer
from .services import AIService
from django.shortcuts import get_object_or_404

class ChatSessionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sessions = ChatSession.objects.filter(user=request.user, is_active=True).order_by('-created_at')
        serializer = ChatSessionSerializer(sessions, many=True)
        return Response(serializer.data)

    def post(self, request):
        title = request.data.get('title', 'New Chat')
        session = ChatSession.objects.create(user=request.user, title=title)
        serializer = ChatSessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ChatMessageAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id):
        session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        content = request.data.get('content')

        if not content:
            return Response({"error": "Content is required"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Save User Message
        ChatMessage.objects.create(session=session, role='user', content=content)

        # 2. Get AI Response
        ai_service = AIService(user=request.user)
        
        # Fetch last 10 messages for context
        history_msgs = ChatMessage.objects.filter(session=session).order_by('-created_at')[:10]
        # Reverse to get chronological order for OpenAI
        formatted_history = [
            {"role": msg.role, "content": msg.content} 
            for msg in reversed(history_msgs)
        ]

        ai_response_text = ai_service.get_chat_response(formatted_history)

        # 3. Save AI Message
        ai_message = ChatMessage.objects.create(session=session, role='assistant', content=ai_response_text)

        serializer = ChatMessageSerializer(ai_message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
