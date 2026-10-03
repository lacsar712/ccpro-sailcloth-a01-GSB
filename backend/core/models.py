from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Loft(models.Model):
    name = models.CharField(max_length=120)
    location = models.CharField(max_length=200, blank=True, default="")
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name


class ClothRoll(models.Model):
    STATUS_RAW = "raw"
    STATUS_DIPPING = "dipping"
    STATUS_CURED = "cured"
    STATUS_CHOICES = [
        (STATUS_RAW, "原布"),
        (STATUS_DIPPING, "浸渍中"),
        (STATUS_CURED, "已固化"),
    ]

    loft = models.ForeignKey(Loft, on_delete=models.CASCADE, related_name="rolls")
    roll_code = models.CharField(max_length=40)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_RAW)
    fabric_weight_gsm = models.PositiveIntegerField(default=380)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["loft_id", "roll_code"]
        constraints = [
            models.UniqueConstraint(
                fields=["loft", "roll_code"],
                name="uniq_roll_code_per_loft",
            )
        ]

    def __str__(self):
        return f"{self.loft.name}/{self.roll_code}"


class DipRun(models.Model):
    roll = models.ForeignKey(ClothRoll, on_delete=models.CASCADE, related_name="dip_runs")
    started_at = models.DateTimeField()
    resin_pct = models.DecimalField(max_digits=5, decimal_places=2)
    cure_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"Dip@{self.roll_id} {self.started_at}"


class SaltSprayCoupon(models.Model):
    """盐雾试片检验条：标「已固化」前须有一张未作废且起泡级数为 0 的条。"""

    BLISTER_MIN = 0
    BLISTER_MAX = 5

    roll = models.ForeignKey(
        ClothRoll, on_delete=models.CASCADE, related_name="salt_spray_coupons"
    )
    coupon_no = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    blister_grade = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(BLISTER_MIN), MaxValueValidator(BLISTER_MAX)]
    )
    inspected_at = models.DateTimeField()
    inspector = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="salt_spray_coupons",
    )
    voided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["roll_id", "coupon_no"]
        constraints = [
            models.UniqueConstraint(
                fields=["roll", "coupon_no"],
                condition=models.Q(voided_at__isnull=True),
                name="uniq_active_coupon_no_per_roll",
            )
        ]

    def __str__(self):
        return f"Coupon@{self.roll_id}#{self.coupon_no} 起泡{self.blister_grade}级"
