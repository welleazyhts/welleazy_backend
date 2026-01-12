from django.shortcuts import render
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.core.paginator import Paginator
from .models import PharmacyVendor, PharmacyCategory, PharmacyBanner, Medicine , MedicineDetails , MedicineCoupon
from .serializers import (
    PharmacyVendorSerializer,
    PharmacyCategorySerializer,
    PharmacyBannerSerializer,
    MedicineSerializer,
    MedicinesDetailsSerializer,
    MedicineCouponSerializer,
)
import requests
from django.shortcuts import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser
from .utils import generate_coupon_code, generate_coupon_name





# CLIENT API

class SyncPharmacyDataAPIView(APIView):
    def get(self, request):
        response = requests.get("CLIENT_API_URL")
        data = response.json()

        for item in data.get("products", []):
            Medicine.objects.update_or_create(
                external_id=item["id"],
                defaults={
                    "name": item["name"],
                    "mrp_price": item["mrp"],
                    "selling_price": item["price"],
                    "discount_percent": item.get("discount", 0),
                }
            )
        return Response({"message": "Synced successfully"})


# BANNERS
class PharmacyBannerListAPIView(generics.ListAPIView):
    queryset = PharmacyBanner.objects.all().order_by("-created_at")
    serializer_class = PharmacyBannerSerializer


class CreatePharmacyBannerAPIView(APIView):
    def post(self, request):
        serializer = PharmacyBannerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=self.request.user)
            return Response({"message": "Banner created successfully", "data": serializer.data}, status=201)
        return Response(serializer.errors, status=400)

class UpdatePharmacyBannerAPIView(APIView):
    def put(self, request, pk):
        try:
            banner = PharmacyBanner.objects.get(id=pk)
        except PharmacyBanner.DoesNotExist:
            return Response({"error": "Banner not found"}, status=404)

        serializer = PharmacyBannerSerializer(banner, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Banner updated", "data": serializer.data})
        return Response(serializer.errors, status=400)

class DeletePharmacyBannerAPIView(APIView):
    def delete(self, request, pk):
        try:
            banner = PharmacyBanner.objects.get(id=pk)
            banner.delete()
            return Response({"message": "Banner deleted successfully"})
        except PharmacyBanner.DoesNotExist:
            return Response({"error": "Banner not found"}, status=404)

# class ActivePharmacyBannerListAPIView(APIView):
#     def get(self, request):
#         banners = PharmacyBanner.objects.filter(is_active=True).order_by("priority")
#         serializer = PharmacyBannerSerializer(banners, many=True)
#         return Response(serializer.data)



# VENDORS
class PharmacyVendorListAPIView(generics.ListAPIView):
    queryset = PharmacyVendor.objects.all()
    serializer_class = PharmacyVendorSerializer


class CreateVendorAPIView(APIView):
    def post(self, request):
        serializer = PharmacyVendorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=self.request.user)
            return Response({"message": "Vendor created", "data": serializer.data}, status=201)
        return Response(serializer.errors, status=400)

class UpdateVendorAPIView(APIView):
    def put(self, request, pk):
        try:
            vendor = PharmacyVendor.objects.get(id=pk)
        except PharmacyVendor.DoesNotExist:
            return Response({"error": "Vendor not found"}, status=404)

        serializer = PharmacyVendorSerializer(vendor, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(created_by=self.request.user)
            return Response({"message": "Vendor updated", "data": serializer.data})

        return Response(serializer.errors, status=400)


class DeleteVendorAPIView(APIView):
    def delete(self, request, pk):
        try:
            vendor = PharmacyVendor.objects.get(id=pk)
            vendor.delete()
            return Response({"message": "Vendor deleted"})
        except PharmacyVendor.DoesNotExist:
            return Response({"error": "Vendor not found"}, status=404)

class VendorMedicineListAPIView(APIView):
    def post(self, request):
        vendor_id = request.data.get("vendor_id")
        page = int(request.data.get("page", 1))
        page_size = int(request.data.get("page_size", 20))

        if not vendor_id:
            return Response({"error": "vendor_id is required"}, status=400)

        try:
            vendor = PharmacyVendor.objects.get(id=vendor_id)
        except PharmacyVendor.DoesNotExist:
            return Response({"error": "Vendor not found"}, status=404)

        queryset = Medicine.objects.filter(vendor=vendor)

        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        data = {
            "vendor": PharmacyVendorSerializer(vendor).data,
            "total_items": paginator.count,
            "total_pages": paginator.num_pages,
            "current_page": page,
            "items": MedicineSerializer(page_obj, many=True).data
        }

        return Response(data)

class VendorSyncAPIView(APIView):
    

    def post(self, request):
        vendor_id = request.data.get("vendor_id")
        api_url = request.data.get("client_api_url")

        if not vendor_id or not api_url:
            return Response({"error": "vendor_id and client_api_url are required"}, status=400)

        try:
            vendor = PharmacyVendor.objects.get(id=vendor_id)
        except PharmacyVendor.DoesNotExist:
            return Response({"error": "Vendor not found"}, status=404)

        # FUTURE: integrate client API request
        # response = requests.get(api_url)
        # Parse data -> Sync -> Create products
        # 
        return Response({"message": "Vendor sync scheduled/placeholder"})




# CATEGORIES
class PharmacyCategoryListAPIView(generics.ListAPIView):
    queryset = PharmacyCategory.objects.all()
    serializer_class = PharmacyCategorySerializer

class CreateCategoryAPIView(APIView):

    def post(self, request):
        serializer = PharmacyCategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=self.request.user)
            return Response({"message": "Category created", "data": serializer.data}, status=201)
        return Response(serializer.errors, status=400)

class UpdateCategoryAPIView(APIView):

    def put(self, request, pk):
        try:
            category = PharmacyCategory.objects.get(id=pk)
        except PharmacyCategory.DoesNotExist:
            return Response({"error": "Category not found"}, status=404)

        serializer = PharmacyCategorySerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Category updated", "data": serializer.data})
        return Response(serializer.errors, status=400)

class DeleteCategoryAPIView(APIView):

    def delete(self, request, pk):
        try:
            category = PharmacyCategory.objects.get(id=pk)
            category.delete()
            return Response({"message": "Category deleted"}, status=200)
        except PharmacyCategory.DoesNotExist:
            return Response({"error": "Category not found"}, status=404)




# MEDICINE FILTER

class PharmacyMedicineListAPIView(generics.ListAPIView):
    queryset = Medicine.objects.all()
    serializer_class = MedicineSerializer


class PharmacyMedicineFilterAPIView(APIView):
    serializer_class = MedicineSerializer
   
    def post(self, request):
        search = request.data.get("search")
        category = request.data.get("category")
        vendor = request.data.get("vendor")
        sort = request.data.get("sort")

        page = int(request.data.get("page", 1))
        page_size = int(request.data.get("page_size", 20))

        queryset = Medicine.objects.all()

        # Search filter
        if search:
            queryset = queryset.filter(name__icontains=search)

        # Category filter
        if category:
            queryset = queryset.filter(category_id=category)

        # Vendor filter
        if vendor:
            queryset = queryset.filter(vendor_id=vendor)

        # Sorting
        if sort == "price_low":
            queryset = queryset.order_by("selling_price")
        elif sort == "price_high":
            queryset = queryset.order_by("-selling_price")
        elif sort == "name":
            queryset = queryset.order_by("name")

        # Pagination
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        data = {
            "total_items": paginator.count,
            "total_pages": paginator.num_pages,
            "current_page": page,
            "page_size": page_size,
            "items": MedicineSerializer(page_obj, many=True).data
        }

        return Response(data, status=status.HTTP_200_OK)


class MedicineCreateAPIView(APIView):
  
    def post(self, request):


        name=request.data.get("name")
        vendor=request.data.get("vendor")
        category=request.data.get("category")


        duplicate_exists=Medicine.objects.filter(name__iexact=name,vendor_id=vendor).exists()

        if duplicate_exists:
            return Response(
                {"error": "Medicine with this name already exists for the vendor."},
                status=status.HTTP_400_BAD_REQUEST
            )
       
       
       
        serializer = MedicineSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=self.request.user)
            return Response(
                {"message": "Medicine created successfully", "data": serializer.data},
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MedicineUpdateAPIView(APIView):

    def put(self, request, pk):
        try:
            medicine = Medicine.objects.get(id=pk)
        except Medicine.DoesNotExist:
            return Response({"error": "Medicine not found"}, status=404)

        # DUPLICATE CHECK
        new_name = request.data.get("name", medicine.name)
        new_vendor = request.data.get("vendor", medicine.vendor_id)

        duplicate_exists = Medicine.objects.filter(
            name__iexact=new_name,
            vendor_id=new_vendor
        ).exclude(id=pk).exists()

        if duplicate_exists:
            return Response(
                {"error": "Another medicine with the same name and vendor already exists."},
                status=400
            )

        # APPLY UPDATE
        serializer = MedicineSerializer(medicine, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Medicine updated successfully",
                "data": serializer.data
            }, status=200)

        return Response(serializer.errors, status=400)


class MedicineDeleteAPIView(APIView):

    def delete(self, request, pk):
        try:
            medicine = Medicine.objects.get(id=pk)
            medicine.delete()
            return Response({"message": "Medicine deleted"}, status=200)
        except Medicine.DoesNotExist:
            return Response({"error": "Medicine not found"}, status=404)


class MedicineDetailAPIView(APIView):

    def get(self, request, medicine_name):
        medicine_name=medicine_name.strip()
        try:
            medicine = Medicine.objects.get(name__iexact=medicine_name)
        except Medicine.DoesNotExist:
            return Response({"error": "Medicine not found"}, status=404)
        
        MedicineDetails.objects.get_or_create(medicine=medicine)

        serializer = MedicineSerializer(medicine)
        return Response(serializer.data)
    

class MedicineDetailsCreateAPIView(APIView):

    def post(self, request, medicine_id):
        # 1. Validate medicine
        try:
            medicine = Medicine.objects.get(id=medicine_id)
        except Medicine.DoesNotExist:
            return Response({"error": "Medicine not found"}, status=404)

        # 2. Fetch existing or create new details instance
        details, created = MedicineDetails.objects.get_or_create(medicine=medicine)

        # 3. Serialize + update
        serializer = MedicinesDetailsSerializer(details, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(MedicineSerializer(medicine).data , status=200)
    

class MedicineDetailsUpdateAPIView(APIView):
    
    def patch(self, request, medicine_id):
        try:
            medicine = Medicine.objects.get(id=medicine_id)
        except Medicine.DoesNotExist:
            return Response({"error": "Medicine not found"}, status=404)

        try:
            details = MedicineDetails.objects.get(medicine=medicine)
        except MedicineDetails.DoesNotExist:
            return Response({"error": "Details not found, create first"}, status=404)

        serializer = MedicinesDetailsSerializer(details, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(MedicineSerializer(medicine).data, status=200)



# APPOLO MEDICINE COUPON GENERATION


class CreateMedicineCouponAPIView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):

        coupon_type = request.data.get("coupon_type")  
        vendor_id = request.data.get("vendor")

        # Validate vendor
        if not vendor_id:
            return Response({"error": "Vendor is required"}, status=400)

        try:
            vendor = PharmacyVendor.objects.get(id=vendor_id)
        except PharmacyVendor.DoesNotExist:
            return Response({"error": "Invalid vendor selected"}, status=400)

        # Read fields coming from frontend
        name = request.data.get("name")
        email = request.data.get("email")
        contact = request.data.get("contact_number")
        state = request.data.get("state")
        city = request.data.get("city")
        address = request.data.get("address")
        medicine_name = request.data.get("medicine_name")
        relationship = request.data.get("relationship")
        document = request.FILES.get("document")

        # Validate mandatory fields
        if not name:
            return Response({"error": "Name is required"}, status=400)
        if not email:
            return Response({"error": "Email is required"}, status=400)
        if not contact:
            return Response({"error": "Contact number is required"}, status=400)
        if not state:
            return Response({"error": "State is required"}, status=400)
        if not city:
            return Response({"error": "City is required"}, status=400)
        if not address:
            return Response({"error": "Address is required"}, status=400)
        if not medicine_name:
            return Response({"error": "Medicine name is required"}, status=400)

        # Dependant: relationship is mandatory
        if coupon_type == "dependent" and not relationship:
            return Response({"error": "Relationship is required for dependant"}, status=400)

        # Check if medicine exists for vendor
        medicine_exists = Medicine.objects.filter(
            name__iexact=medicine_name,
            vendor=vendor
        ).exists()

        if not medicine_exists:
            return Response(
                {"error": "Medicine does not exist for this vendor"},
                status=404
            )
        
          # DUPLICATE COUPON CHECK
        duplicate = MedicineCoupon.objects.filter(
            user=request.user,
            vendor=vendor,
            medicine_name__iexact=medicine_name,
            coupon_type=coupon_type
        ).exists()

        if duplicate:
            return Response(
                {"error": "Coupon already exists for this information"},
                status=400
            )

        # Generate coupon
        coupon_code = generate_coupon_code()
        coupon_name = generate_coupon_name()

        # Create coupon
        coupon = MedicineCoupon.objects.create(
            user=request.user,
            vendor=vendor,
            coupon_type=coupon_type,
            coupon_code=coupon_code,
            coupon_name=coupon_name,
            name=name,
            email=email,
            contact_number=contact,
            state=state,
            city=city,
            address=address,
            medicine_name=medicine_name,
            relationship=relationship,
            document=document,
            created_by=request.user
        )

        return Response({
            "message": "Medicine coupon generated successfully",
            "order_id": f"#{coupon_code}",
            "coupon_name": coupon_name,
            "data": MedicineCouponSerializer(coupon).data
        }, status=201)




class MedicineCouponDetailAPIView(APIView):

    def get(self, request, coupon_code):
        try:
            coupon = MedicineCoupon.objects.get(coupon_code=coupon_code)
        except MedicineCoupon.DoesNotExist:
            return Response({"error": "Invalid coupon"}, status=404)

        data = MedicineCouponSerializer(coupon).data

        return Response({
            "message": "Coupon details fetched successfully",
            "data": data
        }
, status=200)
    

class CouponListAPIView(generics.ListAPIView):
    queryset = MedicineCoupon.objects.all()
    serializer_class = MedicineCouponSerializer
