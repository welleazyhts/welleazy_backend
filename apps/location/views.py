from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import State, City
from .serializers import StateSerializer, CitySerializer
from apps.common.permissions import ReadOnlyOrAuthenticated


class StateViewSet(viewsets.ModelViewSet):
    permission_classes = [ReadOnlyOrAuthenticated]
    serializer_class = StateSerializer
    queryset = State.objects.filter(deleted_at__isnull=True).order_by("name")
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_active']
    search_fields = ['name']

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )

    def perform_update(self, serializer):
        serializer.save(
            updated_by=self.request.user
        )



class CityViewSet(viewsets.ModelViewSet):
    permission_classes = [ReadOnlyOrAuthenticated]
    serializer_class = CitySerializer
    queryset = City.objects.filter(deleted_at__isnull=True).order_by("name")
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_active', 'state']
    search_fields = ['name', 'state__name']

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )

    def perform_update(self, serializer):
        serializer.save(
            updated_by=self.request.user
        )

    @action(detail=False, methods=["get"], url_path="by-state")
    def by_state(self, request):
        state_id = request.query_params.get("state_id")

        if not state_id:
            return Response({"detail": "state_id is required"}, status=400)

        cities = City.objects.filter(state_id=state_id, deleted_at__isnull=True)
        return Response(CitySerializer(cities, many=True).data)

