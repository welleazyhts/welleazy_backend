from django.db import models
from django.conf import settings
from apps.common.models import BaseModel
from apps.dependants.models import Dependant


class HealthAssessment(BaseModel):
    
    # 1–2: For whom (self/dependant) – details from user/dependant tables
    
    STATUS_CHOICES = (
        ("in_process", "In Process"),
        ("active", "Active"),
        ("archived", "Archived"),
    )

    MOOD_CHOICES = (
        (1, "Very Bad"),
        (2, "Bad"),
        (3, "Okay"),
        (4, "Good"),
        (5, "Very Good"),
    )

    HEIGHT_UNIT_CHOICES = (
        ("feet", "Feet & Inches"),
        ("cm", "Centimeters"),
    )
    
    BMI_CATEGORY_CHOICES = [
        ("underweight", "Underweight"),
        ("normal", "Normal"),
        ("overweight", "Overweight"),
        ("obese", "Obese"),
    ]
    
    PRESENTING_ILLNESS_CHOICES = (
        ("cough", "Cough"),
        ("cold", "Cold"),
        ("fever", "Fever"),
        ("diabetes", "Diabetes"),
        ("hypertension", "Hypertension"),
        ("asthma", "Asthma"),
        ("fine", "I am fine"),
        ("other", "Other"),
    )

    FREQ5_CHOICES = (
        ("never", "Never or almost never"),
        ("occasionally", "Occasionally"),
        ("often", "Often"),
        ("very_often", "Very often"),
        ("always", "Always or almost always"),
    )

    WATER_CHOICES = (
        ("lt_9", "Less than 9 glasses"),
        ("gt_9", "More than 9 glasses"),
    )

    SLEEP_HOURS_CHOICES = (
        ("lt_7", "Less than 7 hours"),
        ("gt_7", "More than 7 hours"),
    )

    WAKEUP_REASON_CHOICES = (
        ("excessive_urination", "Excessive Urination"),
        ("breathing_difficulty", "Breathing Difficulty"),
        ("stress", "Stress"),
        ("body_over_heat", "Body Over Heat"),
        ("indigestion", "Indigestion"),
        ("anxiety_depression", "Anxiety / Depression"),
    )
    
    CHECKUP_FREQ_CHOICES = (
        ("six_months", "Every six months"),
        ("yearly", "Yearly once"),
        ("few_times", "Few times in life"),
    )

    DURATION4_CHOICES = (
        ("lt_30", "Less than 30 mins"),
        ("30_60", "30 mins - 1 hr"),
        ("gt_60", "More than 1 hr"),
        ("none", "Not really"),
    )

    OTHER_ACTIVITY_CHOICES = (
        ("none", "None"),
        ("running", "Running"),
        ("sports", "Playing any sport"),
        ("cycling", "Cycling"),
        ("gymnastics", "Gymnastics"),
        ("other", "Other"),
    )

    RISK_CATEGORY_CHOICES = (
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    )
    
    ALCOHOL_FREQUENCY_CHOICES = (
    ("daily", "Daily"),
    ("weekly", "Weekly once"),
    ("occasional", "Occasional drinker"),
    )

    ALCOHOL_DURATION_CHOICES = (
        ("lt_1", "<1yr"),
        ("1_5", "1–5yrs"),
        ("5_10", "5–10yrs"),
        ("gt_10", ">10yrs"),
    )

    ALCOHOL_QUIT_CHOICES = (
        ("lt_1", "<1yr"),
        ("1_3", "1–3yrs"),
        ("3_5", "3–5yrs"),
        ("gt_5", ">5yrs"),
    )

    TOBACCO_TYPE_CHOICES = (
        ("cigarette", "Cigarette"),
        ("bedi", "Bedi"),
        ("gutka", "Gutka"),
        ("raw_tobacco", "Raw Tobacco"),
        ("pan", "Pan"),
    )

    TOBACCO_DURATION_CHOICES = (
        ("lt_1", "<1yr"),
        ("1_5", "1–5yrs"),
        ("5_10", "5–10yrs"),
        ("gt_10", ">10yrs"),
    )

    TOBACCO_QUIT_CHOICES = (
        ("lt_1", "<1yr"),
        ("1_3", "1–3yrs"),
        ("3_5", "3–5yrs"),
        ("gt_5", ">5yrs"),
    )

    URINE_DIFFICULTY_REASON_CHOICES = (
        ("flow_difficulty", "Difficulty in flow of urine"),
        ("blood_urination", "Blood tinged urination"),
        ("pain_while_urinating", "Pain while urinating"),
    )

    WORK_STRESS_REASON_CHOICES = (
        ("increased_workload", "Increased Workload"),
        ("long_working_hours", "Long Working Hours"),
        ("health_issues", "Any Health Issues"),
        ("financial_issue", "Financial Issue"),
        ("others", "Others"),
    )


    # Owner / subject
    FOR_WHOM_CHOICES = (
        ("self", "Self"),
        ("dependant", "Dependant"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="health_assessments",
    )

    for_whom = models.CharField(
        max_length=20,
        choices=FOR_WHOM_CHOICES,
        default="self"
    )
 
    dependant = models.ForeignKey(
        Dependant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="health_assessments",
    )

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="in_process"
    )
    current_step = models.PositiveSmallIntegerField(default=1)  # 1–15

    # STEP 3: Mood today
    mood_today = models.PositiveSmallIntegerField(
        choices=MOOD_CHOICES, null=True, blank=True
    )

    # STEP 4: Basic profile
    height_unit = models.CharField(
        max_length=10, choices=HEIGHT_UNIT_CHOICES, null=True, blank=True
    )
    height_feet = models.PositiveSmallIntegerField(null=True, blank=True)
    height_inches = models.PositiveSmallIntegerField(null=True, blank=True)
    height_cm = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    weight_kg = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    bmi = models.CharField(
        max_length=20, choices=BMI_CATEGORY_CHOICES, null=True, blank=True
    )

    # “How do you feel about your health?”
    health_opinion = models.CharField(
        max_length=20, null=True, blank=True
    )  # e.g. "healthy" / "unhealthy"

    # STEP 5: Presenting illness

    presenting_illness = models.CharField(
        max_length=50,
        choices=PRESENTING_ILLNESS_CHOICES,
        null=True,
        blank=True
    )

    presenting_illness_other = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    # STEP 6: Past history
    chronic_illness = models.BooleanField(null=True, blank=True)
    chronic_illness_details = models.CharField(max_length=255, null=True, blank=True)

    surgery_history = models.BooleanField(null=True, blank=True)
    surgery_history_details = models.CharField(max_length=255, null=True, blank=True)

    # STEP 7: Sleep assessment
    sleep_hours = models.CharField(
        max_length=10, choices=SLEEP_HOURS_CHOICES, null=True, blank=True
    )
    wakeup_midnight = models.BooleanField(null=True, blank=True)
    wakeup_midnight_reasons = models.CharField(max_length=255, choices=WAKEUP_REASON_CHOICES, null=True, blank=True)

    tired_morning = models.BooleanField(null=True, blank=True)

    # STEP 8: Eating habits
    junk_food_freq = models.CharField(
        max_length=20, choices=FREQ5_CHOICES, null=True, blank=True
    )
    fruits_veg_freq = models.CharField(
        max_length=20, choices=FREQ5_CHOICES, null=True, blank=True
    )
    milk_dairy_freq = models.CharField(
        max_length=20, choices=FREQ5_CHOICES, null=True, blank=True
    )
    water_intake = models.CharField(
        max_length=10, choices=WATER_CHOICES, null=True, blank=True
    )
    is_veg = models.BooleanField(
        default=True
    )  # True = Veg, False = Non-veg
    non_veg_freq = models.CharField(
        max_length=20, choices=FREQ5_CHOICES, blank=True, null=True
    )

    # STEP 9: Drinking habits
    alcohol_current = models.BooleanField(null=True, blank=True)
    alcohol_frequency = models.CharField(max_length=20, choices=ALCOHOL_FREQUENCY_CHOICES, null=True, blank=True)  
    alcohol_quantity = models.CharField(max_length=10, null=True, blank=True)  
    alcohol_duration = models.CharField(max_length=20, choices=ALCOHOL_DURATION_CHOICES, null=True, blank=True)
    alcohol_planning_quit = models.BooleanField(null=True, blank=True)

    alcohol_past = models.BooleanField(null=True, blank=True)
    alcohol_quit_period = models.CharField(max_length=20, choices=ALCOHOL_QUIT_CHOICES, null=True, blank=True)

    # STEP 10: Smoking / tobacco
    tobacco_current = models.BooleanField(null=True, blank=True)
    tobacco_type = models.CharField(max_length=20, choices=TOBACCO_TYPE_CHOICES, null=True, blank=True)
    tobacco_duration = models.CharField(max_length=20, choices=TOBACCO_DURATION_CHOICES, null=True, blank=True)
    tobacco_planning_quit = models.BooleanField(null=True, blank=True)

    tobacco_quit = models.BooleanField(null=True, blank=True)
    tobacco_quit_period = models.CharField(max_length=20, choices=TOBACCO_QUIT_CHOICES, null=True, blank=True)


    # STEP 11: Hereditary / meds
    family_chronic_illness = models.BooleanField(null=True, blank=True)
    checkup_frequency = models.CharField(
        max_length=20, choices=CHECKUP_FREQ_CHOICES, null=True, blank=True
    )
    taking_regular_meds = models.BooleanField(null=True, blank=True)
    stopped_meds_without_doctor = models.BooleanField(null=True, blank=True)
    other_alt_medicine = models.BooleanField(null=True, blank=True)

    # STEP 12: Bowel / bladder
    difficulty_urine = models.BooleanField(null=True, blank=True)
    difficulty_urine_reasons = models.CharField(max_length=255, choices=URINE_DIFFICULTY_REASON_CHOICES, null=True, blank=True)

    difficulty_stools = models.BooleanField(null=True, blank=True)

    # STEP 13: Fitness profile
    stretch_duration = models.CharField(
        max_length=10, choices=DURATION4_CHOICES, null=True, blank=True
    )
    cardio_duration = models.CharField(
        max_length=10, choices=DURATION4_CHOICES, null=True, blank=True
    )
    strength_duration = models.CharField(
        max_length=10, choices=DURATION4_CHOICES, null=True, blank=True
    )
    walking_duration = models.CharField(
        max_length=10, choices=DURATION4_CHOICES, null=True, blank=True
    )
    other_activity = models.CharField(
        max_length=20, choices=OTHER_ACTIVITY_CHOICES, null=True, blank=True
    )

    # STEP 14: Mental wellness
    low_interest = models.BooleanField(null=True, blank=True)
    depressed = models.BooleanField(null=True, blank=True)
    sleep_appetite_issue = models.BooleanField(null=True, blank=True)
    low_energy = models.BooleanField(null=True, blank=True)
    anxious = models.BooleanField(null=True, blank=True)

    # STEP 15: Employee wellness
    work_stress_affecting_life = models.BooleanField(null=True, blank=True)
    work_stress_reasons = models.CharField(max_length=255, choices=WORK_STRESS_REASON_CHOICES, null=True, blank=True)

    # Result / report
    total_score = models.IntegerField(null=True, blank=True)
    risk_category = models.CharField(
        max_length=10, choices=RISK_CATEGORY_CHOICES, null=True, blank=True
    )

    # optional: text/PDF report
    report_file = models.FileField(
        upload_to="health_assessments/",
        null=True,
        blank=True,
    )

    def __str__(self):
        if self.for_whom == "self":
            who = "Self"
        else:
            who = self.dependant.name if self.dependant else "Unknown"
        return f"HRA #{self.id} for {who}"


# FAMILY ILLNESS RECORD MODEL

class FamilyIllnessRecord(models.Model):
    DISEASE_CHOICES = (
        ("heart_disease", "Heart Disease"),
        ("stroke", "Stroke"),
        ("hypertension", "Hypertension"),
        ("cancer", "Cancer"),
        ("depression", "Depression"),
        ("type2_diabetes", "Type 2 Diabetes"),
        ("arthritis", "Arthritis"),
        ("osteoporosis", "Osteoporosis"),
        ("asthma", "Asthma"),
        ("copd", "Chronic Obstructive Pulmonary Disease (COPD)"),
        ("kidney_disease", "Chronic Kidney Disease"),
        ("oral_disease", "Oral Disease"),
    )

    hra = models.ForeignKey(
        HealthAssessment,
        on_delete=models.CASCADE,
        related_name="family_illness_records"
    )

    dependant = models.ForeignKey(
        Dependant,
        on_delete=models.CASCADE,
        related_name="family_history"
    )

    disease = models.CharField(max_length=100, choices=DISEASE_CHOICES)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.dependant.name} - {self.get_disease_display()}"
