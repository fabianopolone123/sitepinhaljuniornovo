from django.contrib.auth.models import User
from datetime import date
from decimal import Decimal
from django.utils import timezone

from django.db import models


SEX_CHOICES = [
    ("M", "Masculino"),
    ("F", "Feminino"),
]

MEDICAL_DISEASES = [
    ("catapora", "Catapora"),
    ("meningite", "Meningite"),
    ("hepatite", "Hepatite"),
    ("dengue", "Dengue"),
    ("pneumonia", "Pneumonia"),
    ("malaria", "Malária"),
    ("febre_amarela", "Febre amarela"),
    ("h1n1", "H1N1"),
    ("colera", "Cólera"),
    ("rubeola", "Rubéola"),
    ("sarampo", "Sarampo"),
    ("tetano", "Tétano"),
    ("variola", "Varíola"),
    ("coqueluche", "Coqueluche"),
    ("difteria", "Difteria"),
    ("caxumba", "Caxumba"),
    ("rinite", "Rinite"),
    ("bronquite", "Bronquite"),
]

BLOOD_TYPE_CHOICES = [
    ("A+", "A+"),
    ("A-", "A-"),
    ("B+", "B+"),
    ("B-", "B-"),
    ("AB+", "AB+"),
    ("AB-", "AB-"),
    ("O+", "O+"),
    ("O-", "O-"),
]

DISABILITY_CHOICES = [
    ("none", "Sem deficiência física"),
    ("cadeirante", "Cadeirante"),
    ("visual", "Visual"),
    ("auditivo", "Auditivo"),
    ("fala", "Fala / dificuldade"),
    ("outra", "Outra deficiência"),
]


class Responsible(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="responsavel")
    cpf = models.CharField(max_length=14, unique=True)
    telefone = models.CharField(max_length=20)
    whatsapp = models.CharField(max_length=20)
    endereco = models.CharField(max_length=255)
    sexo = models.CharField(max_length=1, choices=SEX_CHOICES, default="M")
    signature_image = models.ImageField(upload_to="signatures/%Y/%m", blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} ({self.user.get_full_name()})"


class Adventurer(models.Model):
    responsible = models.ForeignKey(Responsible, on_delete=models.CASCADE, related_name="adventureiros")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    document = models.CharField(max_length=50)
    birth_date = models.DateField()
    allergies = models.TextField()
    medication = models.TextField()
    observation = models.TextField()
    emergency_name = models.CharField(max_length=120)
    emergency_phone = models.CharField(max_length=20)
    emergency_whatsapp = models.CharField(max_length=20)
    photo = models.ImageField(upload_to="adventure_photos/%Y/%m")
    sexo = models.CharField(max_length=1, choices=SEX_CHOICES, default="M")

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.responsible})"


class MedicalRecord(models.Model):
    adventurer = models.OneToOneField(Adventurer, on_delete=models.CASCADE, related_name="medical_record")
    has_health_plan = models.BooleanField(default=False)
    health_plan_name = models.CharField(max_length=140, blank=True)
    health_plan_card = models.CharField(max_length=140, blank=True)
    sus_card = models.CharField(max_length=140, blank=True)

    catapora = models.BooleanField(default=False)
    meningite = models.BooleanField(default=False)
    hepatite = models.BooleanField(default=False)
    dengue = models.BooleanField(default=False)
    pneumonia = models.BooleanField(default=False)
    malaria = models.BooleanField(default=False)
    febre_amarela = models.BooleanField(default=False)
    h1n1 = models.BooleanField(default=False)
    colera = models.BooleanField(default=False)
    rubeola = models.BooleanField(default=False)
    sarampo = models.BooleanField(default=False)
    tetano = models.BooleanField(default=False)
    variola = models.BooleanField(default=False)
    coqueluche = models.BooleanField(default=False)
    difteria = models.BooleanField(default=False)
    caxumba = models.BooleanField(default=False)
    rinite = models.BooleanField(default=False)
    bronquite = models.BooleanField(default=False)

    allergy_cutanea = models.BooleanField(default=False)
    allergy_cutanea_detail = models.CharField(max_length=255, blank=True)
    allergy_alimentar = models.BooleanField(default=False)
    allergy_alimentar_detail = models.CharField(max_length=255, blank=True)
    allergy_medicamento = models.BooleanField(default=False)
    allergy_medicamento_detail = models.CharField(max_length=255, blank=True)

    disability_type = models.CharField(max_length=20, choices=DISABILITY_CHOICES, default="none")

    heart_problem = models.BooleanField(default=False)
    heart_medication = models.CharField(max_length=255, blank=True)
    diabetic = models.BooleanField(default=False)
    diabetic_medication = models.CharField(max_length=255, blank=True)
    genital_problem = models.BooleanField(default=False)
    genital_medication = models.CharField(max_length=255, blank=True)
    psychological_problem = models.BooleanField(default=False)
    psychological_medication = models.CharField(max_length=255, blank=True)

    other_health_problem = models.BooleanField(default=False)
    other_health_problem_detail = models.TextField(blank=True)
    other_medication = models.BooleanField(default=False)
    other_medication_detail = models.TextField(blank=True)

    recent_health_issue = models.BooleanField(default=False)
    recent_health_issue_detail = models.TextField(blank=True)
    recent_medication = models.BooleanField(default=False)
    recent_medication_detail = models.TextField(blank=True)
    recent_injury = models.BooleanField(default=False)
    recent_injury_detail = models.TextField(blank=True)
    surgery = models.BooleanField(default=False)
    surgery_detail = models.TextField(blank=True)
    recent_change = models.BooleanField(default=False)
    recent_change_detail = models.TextField(blank=True)

    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPE_CHOICES, blank=True)

    declaration_city = models.CharField(max_length=140, default="São Carlos")
    declaration_date = models.DateField(default=date.today)
    signature_data = models.TextField(blank=True)

    class Meta:
        verbose_name = "Ficha médica"
        verbose_name_plural = "Fichas médicas"

    def __str__(self):
        return f"Ficha médica de {self.adventurer}"


class MonthlyFee(models.Model):
    PENDING = "P"
    PAID = "D"

    STATUS_CHOICES = [
        (PENDING, "Pendente"),
        (PAID, "Pago"),
    ]

    responsible = models.ForeignKey(Responsible, on_delete=models.CASCADE, related_name="fees")
    adventurer = models.ForeignKey(Adventurer, on_delete=models.CASCADE, related_name="fees")
    month = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    amount = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("1.50"))
    due_day = models.PositiveSmallIntegerField(default=10)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default=PENDING)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("adventurer", "month", "year")

    def __str__(self):
        return f"{self.adventurer} — {self.get_status_display()} {self.month}/{self.year}"


class PasswordRecovery(models.Model):
    responsible = models.ForeignKey(
        Responsible, on_delete=models.CASCADE, related_name="recoveries"
    )
    code = models.CharField(max_length=4)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def mark_used(self):
        self.used = True
        self.save(update_fields=("used",))

    def is_expired(self):
        from django.utils import timezone

        return self.expires_at < timezone.now()

    def __str__(self):
        return f"{self.responsible.user.username} ({self.responsible.cpf}) — {self.code}"

    @property
    def due_date_display(self):
        return f"{self.due_day:02d}/{self.month:02d}/{self.year}"


class PixCharge(models.Model):
    PENDING = "P"
    PAID = "A"

    STATUS_CHOICES = [
        (PENDING, "PIX pendente"),
        (PAID, "PIX aprovado"),
    ]

    responsible = models.ForeignKey(
        Responsible, on_delete=models.CASCADE, related_name="pix_charges"
    )
    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField()
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default=PENDING)
    mp_payment_id = models.CharField(max_length=64, blank=True, null=True)
    external_reference = models.CharField(max_length=128, unique=True)
    qr_code = models.TextField(blank=True, null=True)
    qr_code_base64 = models.TextField(blank=True, null=True)
    copy_text = models.TextField(blank=True, null=True)
    raw_response = models.JSONField(blank=True, null=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("responsible", "year", "month")

    last_notification = models.TextField(blank=True, null=True)
    last_notification_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"PIX {self.responsible} {self.month}/{self.year} ({self.get_status_display()})"

    def mark_paid(self):
        self.status = self.PAID
        self.approved_at = timezone.now()
        self.save(update_fields=("status", "approved_at"))
