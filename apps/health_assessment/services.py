import io
from django.core.files.base import ContentFile
from django.utils.timezone import localtime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

from .models import HealthAssessment, FamilyIllnessRecord


class HealthAssessmentReportService:

    @classmethod
    def generate_report_file(cls, hra: HealthAssessment):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        title_style = styles["Title"]
        heading_style = styles["Heading2"]
        normal = styles["Normal"]

        story = []

        # ---------- Title ----------
        story.append(Paragraph(f"Health Assessment Report #{hra.id}", title_style))
        story.append(Spacer(1, 0.25 * inch))

        # ---------- Basic Info ----------
        user_name = getattr(hra.user, "name", None) or hra.user.email
        for_whom = "Self" if hra.for_whom == "self" else (hra.dependant.name if hra.dependant else "Unknown")

        story.append(Paragraph(f"<b>Basic Information</b>", heading_style))
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph(f"User: {user_name}", normal))
        story.append(Paragraph(f"For: {for_whom}", normal))
        story.append(Paragraph(f"Generated at: {localtime().strftime('%Y-%m-%d %H:%M')}", normal))
        story.append(Spacer(1, 0.25 * inch))

        # ---------- Summary of Inputs ----------
        story.append(Paragraph("<b>Summary of Your Inputs</b>", heading_style))
        story.append(Spacer(1, 0.15 * inch))

        sections = cls._summarize_inputs(hra)
        for section_title, lines in sections:
            story.append(Paragraph(f"<b>{section_title}</b>", normal))
            story.append(Spacer(1, 0.05 * inch))
            if not lines:
                story.append(Paragraph("- No data provided.", normal))
            else:
                for line in lines:
                    story.append(Paragraph(f"- {line}", normal))
            story.append(Spacer(1, 0.15 * inch))

        # ---------- Advice ----------
        advice_lines = cls._build_advice(hra)

        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph("<b>Personalized Health Advice</b>", heading_style))
        story.append(Spacer(1, 0.1 * inch))

        if not advice_lines:
            story.append(Paragraph("No specific advice at this time. Keep maintaining a healthy lifestyle!", normal))
        else:
            for line in advice_lines:
                story.append(Paragraph(f"- {line}", normal))

        doc.build(story)

        pdf_value = buffer.getvalue()
        buffer.close()

        hra.report_file.save(f"hra-{hra.id}.pdf", ContentFile(pdf_value), save=False)

    @classmethod
    def _summarize_inputs(cls, hra: HealthAssessment):

        sections = []

        # Helpers
        def display(val, display_func):
            return display_func() if val not in (None, "", False) else None

        # ---- Step 3 & 4: Mood + Basic profile ----
        lines = []

        if hra.mood_today:
            lines.append(f"Mood today: {hra.get_mood_today_display()}")

        # Height
        if hra.height_unit == "feet" and hra.height_feet is not None:
            inches = hra.height_inches or 0
            lines.append(f"Height: {hra.height_feet} ft {inches} in")
        elif hra.height_unit == "cm" and hra.height_cm is not None:
            lines.append(f"Height: {hra.height_cm} cm")

        if hra.weight_kg is not None:
            lines.append(f"Weight: {hra.weight_kg} kg")

        if hra.bmi:
            lines.append(f"BMI Category: {hra.get_bmi_display()}")

        if hra.health_opinion:
            lines.append(f"Self-rated health: {hra.health_opinion}")

        sections.append(("Mood & Basic Profile", lines))

        # ---- Step 5 & 6: Presenting illness + Past history ----
        lines = []
        if hra.presenting_illness:
            if hra.presenting_illness == "other" and hra.presenting_illness_other:
                lines.append(f"Presenting illness: Other ({hra.presenting_illness_other})")
            else:
                lines.append(f"Presenting illness: {hra.get_presenting_illness_display()}")

        if hra.chronic_illness is not None:
            if hra.chronic_illness:
                text = "Has chronic illness"
                if hra.chronic_illness_details:
                    text += f" ({hra.chronic_illness_details})"
                lines.append(text)
            else:
                lines.append("No chronic illness history reported")

        if hra.surgery_history is not None:
            if hra.surgery_history:
                text = "History of surgery"
                if hra.surgery_history_details:
                    text += f" ({hra.surgery_history_details})"
                lines.append(text)
            else:
                lines.append("No past surgery history reported")

        sections.append(("Current Symptoms & Past Medical History", lines))

        # ---- Step 7: Sleep ----
        lines = []
        if hra.sleep_hours:
            lines.append(f"Sleep duration: {hra.get_sleep_hours_display()}")

        if hra.wakeup_midnight is not None:
            if hra.wakeup_midnight:
                text = "Wakes up in the middle of the night"
                if hra.wakeup_midnight_reasons:
                    text += f" (reason: {dict(HealthAssessment.WAKEUP_REASON_CHOICES).get(hra.wakeup_midnight_reasons, hra.wakeup_midnight_reasons)})"
                lines.append(text)
            else:
                lines.append("No midnight awakenings reported")

        if hra.tired_morning is not None:
            if hra.tired_morning:
                lines.append("Feels tired on waking in the morning")
            else:
                lines.append("Feels reasonably fresh in the morning")

        sections.append(("Sleep Pattern", lines))

        # ---- Step 8: Eating habits ----
        lines = []
        if hra.junk_food_freq:
            lines.append(f"Junk food frequency: {dict(HealthAssessment.FREQ5_CHOICES).get(hra.junk_food_freq)}")
        if hra.fruits_veg_freq:
            lines.append(f"Fruits & vegetables intake: {dict(HealthAssessment.FREQ5_CHOICES).get(hra.fruits_veg_freq)}")
        if hra.milk_dairy_freq:
            lines.append(f"Milk & dairy intake: {dict(HealthAssessment.FREQ5_CHOICES).get(hra.milk_dairy_freq)}")
        if hra.water_intake:
            lines.append(f"Water intake: {dict(HealthAssessment.WATER_CHOICES).get(hra.water_intake)}")

        if hra.is_veg is not None:
            if hra.is_veg:
                lines.append("Diet type: Vegetarian")
            else:
                text = "Diet type: Non-vegetarian"
                if hra.non_veg_freq:
                    text += f" ({dict(HealthAssessment.FREQ5_CHOICES).get(hra.non_veg_freq)})"
                lines.append(text)

        sections.append(("Eating Habits", lines))

        # ---- Step 9: Drinking habits (Alcohol) ----
        lines = []
        if hra.alcohol_current is not None:
            if hra.alcohol_current:
                text = "Currently consumes alcohol"
                if hra.alcohol_frequency:
                    text += f" ({dict(HealthAssessment.ALCOHOL_FREQUENCY_CHOICES).get(hra.alcohol_frequency)})"
                if hra.alcohol_quantity:
                    text += f", approx. {hra.alcohol_quantity} per occasion"
                if hra.alcohol_duration:
                    text += f", since {dict(HealthAssessment.ALCOHOL_DURATION_CHOICES).get(hra.alcohol_duration)}"
                if hra.alcohol_planning_quit is True:
                    text += "; planning to quit"
                lines.append(text)
            else:
                if hra.alcohol_past:
                    text = "Does not drink currently but has consumed alcohol in the past"
                    if hra.alcohol_quit_period:
                        text += f" (quit {dict(HealthAssessment.ALCOHOL_QUIT_CHOICES).get(hra.alcohol_quit_period)})"
                    lines.append(text)
                else:
                    lines.append("No alcohol use reported")

        sections.append(("Alcohol Use", lines))

        # ---- Step 10: Smoking / tobacco ----
        lines = []
        if hra.tobacco_current is not None:
            if hra.tobacco_current:
                text = "Currently using tobacco"
                if hra.tobacco_type:
                    text += f" ({dict(HealthAssessment.TOBACCO_TYPE_CHOICES).get(hra.tobacco_type)})"
                if hra.tobacco_duration:
                    text += f", since {dict(HealthAssessment.TOBACCO_DURATION_CHOICES).get(hra.tobacco_duration)}"
                if hra.tobacco_planning_quit is True:
                    text += "; planning to quit"
                lines.append(text)
            else:
                if hra.tobacco_quit:
                    text = "Has quit tobacco"
                    if hra.tobacco_quit_period:
                        text += f" ({dict(HealthAssessment.TOBACCO_QUIT_CHOICES).get(hra.tobacco_quit_period)})"
                    lines.append(text)
                else:
                    lines.append("No tobacco use reported")

        sections.append(("Smoking / Tobacco Use", lines))

        # ---- Step 11: Family history & medicines ----
        lines = []
        if hra.family_chronic_illness is not None:
            if hra.family_chronic_illness:
                lines.append("Family history of chronic illness:")
                disease_labels = dict(FamilyIllnessRecord.DISEASE_CHOICES)
                for rec in hra.family_illness_records.all():
                    dep_name = rec.dependant.name if rec.dependant else "Family member"
                    disease = disease_labels.get(rec.disease, rec.disease)
                    lines.append(f"  • {dep_name}: {disease}")
            else:
                lines.append("No significant family history reported")

        if hra.checkup_frequency:
            lines.append(f"Health checkup frequency: {dict(HealthAssessment.CHECKUP_FREQ_CHOICES).get(hra.checkup_frequency)}")

        if hra.taking_regular_meds is not None:
            if hra.taking_regular_meds:
                lines.append("Currently on regular medications")
            else:
                lines.append("Not on any regular long-term medications")

        if hra.stopped_meds_without_doctor is not None and hra.stopped_meds_without_doctor:
            lines.append("Has stopped medicines without consulting a doctor earlier")

        if hra.other_alt_medicine is not None and hra.other_alt_medicine:
            lines.append("Uses alternative medicine (Ayurveda/Homeopathy/others)")

        sections.append(("Family History & Medications", lines))

        # ---- Step 12: Bowel / bladder ----
        lines = []
        if hra.difficulty_urine is not None:
            if hra.difficulty_urine:
                text = "Difficulty with urination"
                if hra.difficulty_urine_reasons:
                    text += f" ({dict(HealthAssessment.URINE_DIFFICULTY_REASON_CHOICES).get(hra.difficulty_urine_reasons, hra.difficulty_urine_reasons)})"
                lines.append(text)
            else:
                lines.append("No urinary difficulty reported")

        if hra.difficulty_stools is not None:
            if hra.difficulty_stools:
                lines.append("Reports difficulty passing stools")
            else:
                lines.append("No bowel difficulty reported")

        sections.append(("Bowel & Bladder", lines))

        # ---- Step 13: Fitness ----
        lines = []
        if hra.stretch_duration:
            lines.append(f"Stretching activity: {dict(HealthAssessment.DURATION4_CHOICES).get(hra.stretch_duration)}")
        if hra.cardio_duration:
            lines.append(f"Cardio/aerobic activity: {dict(HealthAssessment.DURATION4_CHOICES).get(hra.cardio_duration)}")
        if hra.strength_duration:
            lines.append(f"Strength training: {dict(HealthAssessment.DURATION4_CHOICES).get(hra.strength_duration)}")
        if hra.walking_duration:
            lines.append(f"Walking: {dict(HealthAssessment.DURATION4_CHOICES).get(hra.walking_duration)}")
        if hra.other_activity:
            lines.append(f"Other activity: {dict(HealthAssessment.OTHER_ACTIVITY_CHOICES).get(hra.other_activity)}")

        sections.append(("Physical Activity & Fitness", lines))

        # ---- Step 14: Mental wellness ----
        lines = []
        if any([
            hra.low_interest, hra.depressed,
            hra.sleep_appetite_issue, hra.low_energy, hra.anxious
        ]):
            lines.append("Some concerns reported in mood/interest/energy/anxiety:")
            if hra.low_interest:
                lines.append("  • Reduced interest or pleasure in activities")
            if hra.depressed:
                lines.append("  • Feeling down, depressed, or hopeless")
            if hra.sleep_appetite_issue:
                lines.append("  • Issues with sleep or appetite")
            if hra.low_energy:
                lines.append("  • Low energy or fatigue")
            if hra.anxious:
                lines.append("  • Feeling anxious or worried often")
        else:
            lines.append("No significant mental wellness concerns reported")

        sections.append(("Mental Wellness", lines))

        # ---- Step 15: Work stress ----
        lines = []
        if hra.work_stress_affecting_life is not None:
            if hra.work_stress_affecting_life:
                text = "Work stress is affecting personal life"
                if hra.work_stress_reasons:
                    text += f" (main reason: {dict(HealthAssessment.WORK_STRESS_REASON_CHOICES).get(hra.work_stress_reasons, hra.work_stress_reasons)})"
                lines.append(text)
            else:
                lines.append("No major impact of work stress on personal life reported")

        sections.append(("Work & Lifestyle", lines))

        return sections

    @classmethod
    def _build_advice(cls, hra: HealthAssessment):
        # Build a list of advice strings based on ALL key fields.
        # This is not a diagnosis, only lifestyle & checkup suggestions.
        advice = []

        # -------- Mood (Step 3) --------
        if hra.mood_today in (1, 2):
            advice.append(
                "You reported feeling low today. Try to prioritise rest, enjoyable activities, and talk to someone you trust. "
                "If this low mood continues for several weeks or affects daily functioning, consider speaking with a mental health professional."
            )
        elif hra.mood_today in (3,):
            advice.append(
                "Your mood is 'okay'. Keep an eye on your energy and interest levels; regular sleep and physical activity can support better mood."
            )
        elif hra.mood_today in (4, 5):
            advice.append(
                "You reported a good mood. Continue habits that support this – such as regular sleep, movement, and meaningful social connections."
            )

        # -------- Weight / BMI (Step 4) --------
        if hra.bmi == "underweight":
            advice.append(
                "Your BMI falls in the underweight range. A nutrition-focused consultation can help ensure you are getting enough calories and nutrients, "
                "especially protein, healthy fats, and micronutrients."
            )
        elif hra.bmi == "overweight":
            advice.append(
                "Your BMI is in the overweight range. Gradual weight reduction through balanced diet and regular physical activity may reduce the risk of "
                "diabetes, hypertension, and joint problems."
            )
        elif hra.bmi == "obese":
            advice.append(
                "Your BMI is in the obese range. Consider working with a doctor or nutritionist to create a personalized weight management plan, "
                "including diet, activity, and regular health checkups."
            )

        if hra.health_opinion and hra.health_opinion.lower() in ("unhealthy", "not_ok", "poor"):
            advice.append(
                "You feel your health is not optimal. It may help to set 1–2 small, realistic goals (e.g., daily walking, better sleep schedule) and "
                "review them with a healthcare provider."
            )

        # -------- Presenting Illness & Past History (Steps 5–6) --------
        if hra.presenting_illness and hra.presenting_illness != "fine":
            advice.append(
                "Since you have reported a current health complaint, please follow up with a doctor if symptoms persist, worsen, or interfere with your daily activities."
            )

        if hra.chronic_illness:
            advice.append(
                "You have a history of chronic illness. Regular follow-up with your doctor, adherence to prescribed medicines, and routine tests are important "
                "to keep it under control."
            )

        if hra.surgery_history:
            advice.append(
                "Past surgery history should be shared with doctors during future consultations, especially before new procedures or prescriptions."
            )

        # -------- Sleep (Step 7) --------
        if hra.sleep_hours == "lt_7":
            advice.append(
                "You report sleeping less than 7 hours. Most adults benefit from 7–9 hours of sleep. "
                "Try maintaining a fixed sleep schedule, limiting late screen time, and avoiding heavy meals right before bed."
            )
        elif hra.sleep_hours == "gt_7":
            advice.append(
                "You are getting more than 7 hours of sleep, which is generally good. Maintain regular timing and a calm pre-bed routine."
            )

        if hra.wakeup_midnight:
            advice.append(
                "Frequent awakenings at night can affect sleep quality. Since you wake up in the middle of the night, "
                "monitor triggers such as late caffeine, heavy meals, stress, or frequent urination, and discuss them with a clinician if persistent."
            )

        if hra.tired_morning:
            advice.append(
                "Feeling tired on waking may reflect poor sleep quality or other health factors. Consider reviewing your bedtime routine, "
                "and speak to a doctor if this continues for several weeks."
            )

        # -------- Eating habits (Step 8) --------
        if hra.junk_food_freq in ("often", "very_often", "always"):
            advice.append(
                "You consume junk or fast foods quite frequently. Try to reduce fried, sugary, and processed items and replace them with home-cooked meals, "
                "whole grains, fruits, and vegetables."
            )
        elif hra.junk_food_freq == "occasionally":
            advice.append(
                "Your junk food intake is occasional. Continue to keep portion sizes moderate and balance them with healthier foods through the week."
            )

        if hra.fruits_veg_freq in ("never", "occasionally"):
            advice.append(
                "Your fruits and vegetable intake seems low. Aim for at least 4–5 servings of fruits and vegetables per day for better immunity, digestion, "
                "and long-term heart health."
            )

        if hra.water_intake == "lt_9":
            advice.append(
                "Your water intake appears on the lower side. Unless restricted by a doctor, try to sip water regularly through the day and keep urine a pale straw colour."
            )

        if hra.is_veg is False and hra.non_veg_freq in ("often", "very_often", "always"):
            advice.append(
                "Frequent non-vegetarian intake is fine if balanced. Prefer grilled/steamed options over deep-fried, and include fish, pulses, and salads to keep meals heart-friendly."
            )

        # -------- Alcohol (Step 9) --------
        if hra.alcohol_current:
            advice.append(
                "You currently consume alcohol. Reducing the number of drinking days and quantity per occasion can protect your liver, heart, and mental health. "
                "If cutting down is difficult, consider professional support."
            )
        elif (hra.alcohol_past and not hra.alcohol_current):
            advice.append(
                "You have stopped drinking alcohol. Maintaining abstinence is very beneficial for your long-term health. Continue avoiding triggers and seeking support if needed."
            )

        # -------- Tobacco (Step 10) --------
        if hra.tobacco_current:
            advice.append(
                "Tobacco use significantly increases the risk of cancer, heart disease, and lung problems. "
                "Quitting completely is one of the best health decisions you can make; discuss cessation options such as counselling or nicotine replacement with a doctor."
            )
        elif (hra.tobacco_quit and not hra.tobacco_current):
            advice.append(
                "You have quit tobacco. This greatly reduces your long-term health risks. Stay away from people or situations that trigger cravings and celebrate this progress."
            )

        # -------- Family history & checkups (Step 11) --------
        if hra.family_chronic_illness:
            advice.append(
                "A family history of chronic diseases means your own risk can be higher. Regular screening (blood pressure, sugar, cholesterol, etc.) and a healthy lifestyle "
                "become especially important."
            )

        if hra.checkup_frequency in ("few_times", None):
            advice.append(
                "You have not been doing regular preventive health checkups. Consider an annual health check including blood pressure, blood sugar, cholesterol, and basic organ function tests."
            )
        elif hra.checkup_frequency in ("yearly", "six_months"):
            advice.append(
                "You are undergoing health checkups at a good frequency. Continue with regular follow-ups and share reports with your doctor."
            )

        if hra.stopped_meds_without_doctor:
            advice.append(
                "You have stopped medicines without consulting a doctor in the past. Always check with your doctor before stopping or changing prescribed medications."
            )

        # -------- Bowel & bladder (Step 12) --------
        if hra.difficulty_urine or hra.difficulty_stools:
            advice.append(
                "You reported difficulty with urination or bowel movements. If this persists, is painful, or involves blood, please consult a doctor promptly for evaluation."
            )

        # -------- Fitness (Step 13) --------
        low_activity = ("none", "lt_30")

        if hra.walking_duration in low_activity and hra.cardio_duration in low_activity:
            advice.append(
                "Your routine physical activity seems low. Aim for at least 150 minutes per week of moderate activity such as brisk walking, spread across most days."
            )
        else:
            if hra.walking_duration not in (None, "", "none") or hra.cardio_duration not in (None, "", "none"):
                advice.append(
                    "You are including some form of regular physical activity. Try to keep it consistent each week and add stretching and strength exercises if possible."
                )

        # -------- Mental wellness (Step 14) --------
        if any([
            hra.low_interest, hra.depressed,
            hra.sleep_appetite_issue, hra.low_energy, hra.anxious
        ]):
            advice.append(
                "You have indicated some mental wellness concerns. If low mood, loss of interest, poor sleep, or anxiety persist beyond 2–3 weeks or interfere with daily life, "
                "consider speaking to a counsellor or mental health professional."
            )

        # -------- Work stress (Step 15) --------
        if hra.work_stress_affecting_life:
            advice.append(
                "Work-related stress is affecting your personal life. Try to introduce boundaries (fixed work hours where possible), short breaks, and relaxation techniques. "
                "If stress feels overwhelming, a counsellor or coach can help you develop coping strategies."
            )

        # -------- If nothing added --------
        if not advice:
            advice.append(
                "No specific high-risk issues were identified from your responses. Continue maintaining healthy habits for sleep, diet, activity, and mental wellbeing, "
                "and consider annual health checkups."
            )

        return advice
