from django.contrib import admin
from apps.pharmacy.models import (
    PharmacyVendor,
    PharmacyCategory,
    PharmacyBanner,
    Medicine,
    MedicineDetails,
    MedicineCoupon,
    PharmacyOrder,
    PharmacyOrderItem,
)

# Import 1MG admin registrations
from apps.pharmacy.onemg_admin import *


class MedicineDetailsInline(admin.StackedInline):
    model = MedicineDetails
    extra = 0


class PharmacyOrderItemInline(admin.TabularInline):
    model = PharmacyOrderItem
    extra = 0
    readonly_fields = ['medicine', 'quantity', 'amount']


@admin.register(PharmacyVendor)
class PharmacyVendorAdmin(admin.ModelAdmin):
    list_display = ['name', 'vendor_type', 'city', 'phone', 'email']
    list_filter = ['vendor_type']
    search_fields = ['name', 'city']


@admin.register(PharmacyCategory)
class PharmacyCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(PharmacyBanner)
class PharmacyBannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'discount_text', 'button_text']
    search_fields = ['title']


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'vendor', 'mrp_price', 'selling_price', 'discount_percent', 'stock_count']
    list_filter = ['category', 'vendor']
    search_fields = ['name', 'description']
    inlines = [MedicineDetailsInline]


@admin.register(MedicineCoupon)
class MedicineCouponAdmin(admin.ModelAdmin):
    list_display = ['coupon_code', 'coupon_name', 'user', 'coupon_type', 'status', 'ordered_date']
    list_filter = ['coupon_type', 'status', 'order_type']
    search_fields = ['coupon_code', 'coupon_name', 'user__email']


@admin.register(PharmacyOrder)
class PharmacyOrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'user', 'patient_name', 'order_type', 'status', 'total_amount', 'ordered_date']
    list_filter = ['status', 'order_type', 'ordered_date']
    search_fields = ['order_id', 'patient_name', 'user__email']
    inlines = [PharmacyOrderItemInline]
    readonly_fields = ['order_id', 'created_at']
