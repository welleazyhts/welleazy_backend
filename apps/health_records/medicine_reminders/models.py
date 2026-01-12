from django.db import models
from django.conf import settings
from apps.common.models import BaseModel


class MedicineReminder(BaseModel):
    # choices
    MEDICINE_TYPE_CHOICES = (
        ("syrup", "Syrup"),
        ("tablet", "Tablet"),
        ("drops", "Drops"),
        ("inhalers", "Inhalers"),
        ("injections", "Injections"),
        ("cream_gel", "Cream/Gel"),
    )

    FREQUENCY_TYPE_CHOICES = (
        ("fixed_times", "Fixed Times"),
        ("interval", "Interval"),
    )

    INTAKE_FREQUENCY_CHOICES = (
        ("once", "Once"),
        ("twice", "Twice"),
        ("thrice", "Thrice"),
        ("four_times", "Four times"),
        ("unknown", "Unknown"),
    )

    INTERVAL_TYPE_CHOICES = (
        ("every_30_minutes", "Every 30 minutes"),
        ("hourly", "Hourly"),
        ("every_4_hours", "Every 4 hours"),
    )

    DURATION_UNIT_CHOICES = (
        ("day", "Day"),
        ("week", "Week"),
        ("month", "Month"),
    )

    DOSAGE_UNIT_CHOICES = (
        ("tablespoons", "Tablespoons"),
        ("tablet", "Tablet"),
        ("drops", "Drops"),
        ("as_directed", "As directed by physician"),
    )

    MEAL_RELATION_CHOICES = (
        ("before_meal", "Before meal"),
        ("after_meal", "After meal"),
        ("with_meal", "With meal"),
        ("none", "No relation"),
    )

    # main fields
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="medicine_reminders",
    )

    medicine_name = models.CharField(max_length=255)
    medicine_type = models.CharField(max_length=20, choices=MEDICINE_TYPE_CHOICES)

    duration_value = models.PositiveIntegerField(default=1)
    duration_unit = models.CharField(
        max_length=10, choices=DURATION_UNIT_CHOICES, default="day"
    )

    start_date = models.DateField()
    end_date = models.DateField()

    frequency_type = models.CharField(max_length=20, choices=FREQUENCY_TYPE_CHOICES)

    # fixed_times
    intake_frequency = models.CharField(
        max_length=20,
        choices=INTAKE_FREQUENCY_CHOICES,
        blank=True,
        null=True,
    )

    # interval
    interval_type = models.CharField(
        max_length=30,
        choices=INTERVAL_TYPE_CHOICES,
        blank=True,
        null=True,
    )
    interval_start_time = models.TimeField(blank=True, null=True)
    interval_end_time = models.TimeField(blank=True, null=True)

    dosage_value = models.PositiveIntegerField(default=1)
    dosage_unit = models.CharField(max_length=20, choices=DOSAGE_UNIT_CHOICES)

    doctor_name = models.CharField(max_length=255, blank=True, null=True)
    appointment_reminder_date = models.DateField(blank=True, null=True)

    current_inventory = models.PositiveIntegerField(default=0)
    remind_when_inventory = models.PositiveIntegerField(default=0)
    medicines_left = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.medicine_name} ({self.user})"


class MedicineReminderTime(BaseModel):
    reminder = models.ForeignKey(
        MedicineReminder,
        on_delete=models.CASCADE,
        related_name="schedule_times",
    )
    time = models.TimeField()
    meal_relation = models.CharField(
        max_length=20,
        choices=MedicineReminder.MEAL_RELATION_CHOICES,
        default="none",
    )

    class Meta:
        ordering = ["time"]

    def __str__(self):
        return f"{self.time} ({self.meal_relation})"


class MedicineReminderDocument(BaseModel):

    reminder = models.ForeignKey(
        MedicineReminder,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    file = models.FileField(upload_to="medicine_reminders/")
