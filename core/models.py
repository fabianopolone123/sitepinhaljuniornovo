from django.contrib.auth.models import User
from decimal import Decimal
from django.utils import timezone

from django.db import models


SEX_CHOICES = [
    ("M", "Masculino"),
    ("F", "Feminino"),
]


class Responsible(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="responsavel")
    cpf = models.CharField(max_length=14, unique=True)
    telefone = models.CharField(max_length=20)
    whatsapp = models.CharField(max_length=20)
    endereco = models.CharField(max_length=255)
    sexo = models.CharField(max_length=1, choices=SEX_CHOICES, default="M")

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
    school = models.CharField(max_length=200, blank=True)
    grade = models.CharField(max_length=80, blank=True)
    bolsa_familia = models.BooleanField(default=False)
    classes_investidas = models.TextField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    neighborhood = models.CharField(max_length=120, blank=True)
    city = models.CharField(max_length=120, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    state = models.CharField(max_length=60, blank=True)
    certidao = models.CharField(max_length=120, blank=True)
    rg = models.CharField(max_length=60, blank=True)
    rg_issuer = models.CharField(max_length=60, blank=True)
    cpf_number = models.CharField(max_length=30, blank=True)
    parent_whatsapp = models.BooleanField(default=False)
    shirt_size = models.CharField(max_length=20, blank=True)
    blood_type = models.CharField(max_length=3, blank=True)
    family_data = models.JSONField(blank=True, null=True)
    medical_data = models.JSONField(blank=True, null=True)
    term_data = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.responsible})"


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


class DirectorApplication(models.Model):
    EDUCATION_CHOICES = [
        ("fundamental", "Ensino Fundamental"),
        ("medio", "Ensino Médio"),
        ("faculdade", "Faculdade"),
    ]

    responsible = models.OneToOneField(
        Responsible, on_delete=models.CASCADE, related_name="director_profile"
    )
    full_name = models.CharField(max_length=200)
    term_nationality = models.CharField(max_length=80, blank=True)
    term_marital_status = models.CharField(max_length=60, blank=True)
    term_rg_number = models.CharField(max_length=30, blank=True)
    term_residence = models.CharField(max_length=255, blank=True)
    term_number = models.CharField(max_length=20, blank=True)
    term_neighborhood = models.CharField(max_length=120, blank=True)
    term_postal_code = models.CharField(max_length=20, blank=True)
    term_municipality = models.CharField(max_length=120, blank=True)
    term_state = models.CharField(max_length=60, blank=True)
    term_cpf = models.CharField(max_length=20, blank=True)
    term_accepted = models.BooleanField(default=False)

    church = models.CharField(max_length=150)
    district = models.CharField(max_length=80)
    street_address = models.CharField(max_length=255)
    house_number = models.CharField(max_length=20)
    neighborhood = models.CharField(max_length=120)
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=120)
    state = models.CharField(max_length=60)
    email = models.EmailField()
    cellphone = models.CharField(max_length=20)
    home_phone = models.CharField(max_length=20, blank=True)
    work_phone = models.CharField(max_length=20, blank=True)
    birth_date = models.DateField()
    volunteer_marital_status = models.CharField(max_length=60)
    director_cpf = models.CharField(max_length=20)
    director_rg = models.CharField(max_length=30)
    spouse = models.CharField(max_length=120, blank=True)
    child_one = models.CharField(max_length=120, blank=True)
    child_two = models.CharField(max_length=120, blank=True)
    health_limitation = models.BooleanField(default=False)
    health_description = models.TextField(blank=True)
    education_level = models.CharField(max_length=20, choices=EDUCATION_CHOICES)
    photo = models.ImageField(
        upload_to="director_photos/%Y/%m", blank=True, null=True
    )
    volunteer_acceptance = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Diretoria — {self.responsible.user.get_full_name()}"
