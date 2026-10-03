from django.contrib import admin

from .models import ClothRoll, DipRun, Loft, SaltSprayCoupon

admin.site.register(Loft)
admin.site.register(ClothRoll)
admin.site.register(DipRun)


@admin.register(SaltSprayCoupon)
class SaltSprayCouponAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "roll",
        "strip_no",
        "blister_grade",
        "inspected_at",
        "inspector",
        "voided_at",
    )
    list_filter = ("blister_grade", "voided_at")
