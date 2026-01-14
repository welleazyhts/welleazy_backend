# app: women_health/models.py
from django.db import models
from django.utils import timezone
from datetime import timedelta

class Symptoms(models.Model):
    #Symptoms that user can select (populated with your list)
    name = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.name


class WomanProfile(models.Model):
    # Profile storing basic info (age)
    # you might want to link to User (ForeignKey) if this is an authenticated feature
    # user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="women_profiles")
    age = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile #{self.id} (age {self.age})"


class CycleEntry(models.Model):
    #A saved tracking entry for a given profile: holds averages, last start and computed predictions
    profile = models.ForeignKey(WomanProfile, on_delete=models.CASCADE, related_name="cycles")
    avg_period_length = models.PositiveSmallIntegerField(help_text="Days of bleeding (e.g. 4)")
    avg_cycle_length = models.PositiveSmallIntegerField(help_text="Days between starts of periods (e.g. 28)")
    last_period_start = models.DateField(help_text="YYYY-MM-DD - first day of last period")
    symptoms = models.ManyToManyField(Symptoms, blank=True, related_name="cycle_entries")

    # computed fields (stored for convenience)
    next_period_start = models.DateField(null=True, blank=True)
    next_period_end = models.DateField(null=True, blank=True)
    ovulation_date = models.DateField(null=True, blank=True)
    fertile_window_start = models.DateField(null=True, blank=True)
    fertile_window_end = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def compute_predictions(self):

        lps = self.last_period_start
        self.next_period_start = lps + timedelta(days=self.avg_cycle_length)
        self.next_period_end = self.next_period_start + timedelta(days=max(self.avg_period_length - 1, 0))
        self.ovulation_date = self.next_period_start - timedelta(days=14)
        self.fertile_window_start = self.ovulation_date - timedelta(days=5)
        self.fertile_window_end = self.ovulation_date

    def save(self, *args, **kwargs):
        # ensure computed fields are set before saving
        self.compute_predictions()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Cycle for profile {self.profile.id} at {self.created_at.date()}"
