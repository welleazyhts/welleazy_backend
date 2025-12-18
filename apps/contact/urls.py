from django.urls import path
from .views import submit_contact

urlpatterns = [
    path("submit/", submit_contact, name="contact-submit"),
]
