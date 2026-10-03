import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SaltSprayCoupon",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("strip_no", models.PositiveIntegerField()),
                (
                    "blister_grade",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (0, "0"),
                            (1, "1"),
                            (2, "2"),
                            (3, "3"),
                            (4, "4"),
                            (5, "5"),
                        ]
                    ),
                ),
                ("inspected_at", models.DateTimeField()),
                ("voided_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "inspector",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="salt_coupons",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "roll",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="salt_coupons",
                        to="core.clothroll",
                    ),
                ),
            ],
            options={
                "ordering": ["roll_id", "strip_no", "-id"],
            },
        ),
        migrations.AddConstraint(
            model_name="saltspraycoupon",
            constraint=models.UniqueConstraint(
                condition=models.Q(("voided_at__isnull", True)),
                fields=("roll", "strip_no"),
                name="uniq_strip_no_per_roll_when_active",
            ),
        ),
        migrations.AddConstraint(
            model_name="saltspraycoupon",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("blister_grade__gte", 0), ("blister_grade__lte", 5)
                ),
                name="blister_grade_0_to_5",
            ),
        ),
    ]
