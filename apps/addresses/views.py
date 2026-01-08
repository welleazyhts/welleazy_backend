# apps/addresses/views.py
from rest_framework.response import Response
from rest_framework import generics, permissions
from rest_framework.exceptions import ValidationError
from .models import Address, AddressType
from .serializers import AddressSerializer, AddressTypeSerializer
from apps.dependants.models import Dependant
from django.shortcuts import get_object_or_404
from apps.common.utils.profile_helper import get_effective_user


class AddressTypeListCreateView(generics.ListCreateAPIView):
    #List or create address types (Home, Office, Other)
    queryset = AddressType.objects.all()
    serializer_class = AddressTypeSerializer
    permission_classes = [permissions.IsAuthenticated]

# SELF ADDRESSES

class SelfAddressListCreateView(generics.ListCreateAPIView):
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Address.objects.filter(user=self.request.user)

        address_type = self.request.query_params.get("address_type")
        if address_type:
            queryset = queryset.filter(address_type_id=address_type)

        return queryset

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response(
            {
                "message": "Address added successfully",
                "data": response.data
            },
            status=response.status_code
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, dependant=None)


class SelfAddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response(
            {
                "message": "Address updated successfully",
                "data": response.data
            },
            status=response.status_code
        )

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response({"message": "Address deleted successfully"}, status=200)
    


# DEPENDANT ADDRESSES


class DependantAddressListCreateView(generics.ListCreateAPIView):
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_dependant(self):
        dependant_id = self.kwargs["dependant_id"]
        return get_object_or_404(
            Dependant,
            id=dependant_id,
            user=self.request.user,
            is_active=True
        )

    def get_queryset(self):
        dependant = self.get_dependant()
        queryset = Address.objects.filter(dependant=dependant)

        address_type = self.request.query_params.get("address_type")
        if address_type:
            queryset = queryset.filter(address_type_id=address_type)

        return queryset

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response(
            {
                "message": "Dependant address added successfully",
                "data": response.data
            },
            status=response.status_code
        )

    def perform_create(self, serializer):
        dependant = self.get_dependant()
        serializer.save(
            user=None,
            dependant=dependant,
        )



class DependantAddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        dependant_id = self.kwargs["dependant_id"]
        return Address.objects.filter(
            dependant_id=dependant_id,
            dependant__user=self.request.user
        )

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response(
            {
                "message": "Dependant address updated successfully",
                "data": response.data
            },
            status=response.status_code
        )

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response({"message": "Dependant address deleted successfully"}, status=200)


# UNIFIED ADDRESS API (Works with Profile Switching) 

class UnifiedAddressListCreateView(generics.ListCreateAPIView):

    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user, dependant_id = get_effective_user(self.request)
        
        if dependant_id:
            # User is switched to a dependant - show only that dependant's addresses
            queryset = Address.objects.filter(dependant_id=dependant_id)
        else:
            # User is on their own profile - show ALL addresses (self + all dependants)
            queryset = Address.objects.filter(user=user)
        
        # Optional filter by address type
        address_type = self.request.query_params.get("address_type")
        if address_type:
            queryset = queryset.filter(address_type_id=address_type)
        
        return queryset

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        
        user, dependant_id = get_effective_user(request)
        message = "Address added successfully"
        if dependant_id:
            dependant = Dependant.objects.get(id=dependant_id)
            message = f"Address added successfully for {dependant.name}"
        
        return Response(
            {
                "message": message,
                "data": response.data
            },
            status=response.status_code
        )

    def perform_create(self, serializer):
        user, dependant_id = get_effective_user(self.request)
        
        if dependant_id:
            # Creating address for dependant
            dependant = Dependant.objects.get(id=dependant_id)
            serializer.save(
                user=None,
                dependant=dependant,
            )
        else:
            # Creating address for main user
            serializer.save(user=user, dependant=None)


class UnifiedAddressDetailView(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user, dependant_id = get_effective_user(self.request)
        
        if dependant_id:
            # User is switched to a dependant - show only that dependant's addresses
            return Address.objects.filter(
                dependant_id=dependant_id,
                dependant__user=user
            )
        else:
            # User is on their own profile - show ALL addresses (self + all dependants)
            return Address.objects.filter(user=user)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response(
            {
                "message": "Address updated successfully",
                "data": response.data
            },
            status=response.status_code
        )

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response({"message": "Address deleted successfully"}, status=200)

