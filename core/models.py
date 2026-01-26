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
    amount = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("1.00"))
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

    def __str__(self):
        return f"PIX {self.responsible} {self.month}/{self.year} ({self.get_status_display()})"

    def mark_paid(self):
        self.status = self.PAID
        self.approved_at = timezone.now()
        self.save(update_fields=("status", "approved_at"))
