from django.shortcuts import render

# Create your views here.

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import WomanProfile, Symptoms, CycleEntry
from .serializers import WomanProfileSerializer, SymptomSerializer, CycleEntrySerializer
from django.shortcuts import get_object_or_404

class SymptomViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Symptoms.objects.all().order_by("name")
    serializer_class = SymptomSerializer

class WomanProfileViewSet(viewsets.ModelViewSet):
    queryset = WomanProfile.objects.all().order_by("-created_at")
    serializer_class = WomanProfileSerializer

    @action(detail=True, methods=["get"])
    def cycles(self, request, pk=None):
        # List all saved cycles for the profile
        profile = self.get_object()
        qs = profile.cycles.all().order_by("-created_at")
        serializer = CycleEntrySerializer(qs, many=True)
        return Response(serializer.data)


class CycleEntryViewSet(viewsets.ModelViewSet):
    queryset = CycleEntry.objects.all().order_by("-created_at")
    serializer_class = CycleEntrySerializer

    def create(self, request, *args, **kwargs):
      
        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=["get"])
    def predictions(self, request, pk=None):
        # Return computed fields for a specific cycle entry (read-only)
        entry = self.get_object()
        serializer = self.get_serializer(entry)
        return Response(serializer.data)
