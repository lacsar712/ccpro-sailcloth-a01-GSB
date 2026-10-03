from rest_framework import serializers

from .models import ClothRoll, DipRun, Loft, SaltSprayCoupon
from .rules import can_mark_roll_cured


class LoftSerializer(serializers.ModelSerializer):
    rollCount = serializers.SerializerMethodField()

    class Meta:
        model = Loft
        fields = ("id", "name", "location", "notes", "rollCount", "created_at")
        read_only_fields = ("id", "rollCount", "created_at")

    def get_rollCount(self, obj):
        if hasattr(obj, "roll_count"):
            return obj.roll_count
        return obj.rolls.count()


class ClothRollSerializer(serializers.ModelSerializer):
    loftId = serializers.PrimaryKeyRelatedField(source="loft", queryset=Loft.objects.all())
    rollCode = serializers.CharField(source="roll_code")
    fabricWeightGsm = serializers.IntegerField(source="fabric_weight_gsm", required=False)
    loftName = serializers.CharField(source="loft.name", read_only=True)

    class Meta:
        model = ClothRoll
        fields = (
            "id",
            "loftId",
            "loftName",
            "rollCode",
            "status",
            "fabricWeightGsm",
            "notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "loftName", "created_at", "updated_at")

    def validate(self, attrs):
        loft = attrs.get("loft") or getattr(self.instance, "loft", None)
        roll_code = attrs.get("roll_code") or getattr(self.instance, "roll_code", None)
        if loft and roll_code:
            qs = ClothRoll.objects.filter(loft=loft, roll_code=roll_code)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({"rollCode": "同一帆布间卷号必须唯一"})

        new_status = attrs.get("status")
        if new_status == ClothRoll.STATUS_CURED:
            roll = self.instance
            if roll is None:
                raise serializers.ValidationError(
                    {"status": "新建布卷不能直接设为已固化"}
                )
            # 合并未提交字段到临时视角：用当前实例校验
            ok, msg = can_mark_roll_cured(roll)
            if not ok:
                raise serializers.ValidationError({"status": msg})
        return attrs


class DipRunSerializer(serializers.ModelSerializer):
    rollId = serializers.PrimaryKeyRelatedField(
        source="roll", queryset=ClothRoll.objects.all()
    )
    startedAt = serializers.DateTimeField(source="started_at")
    resinPct = serializers.DecimalField(source="resin_pct", max_digits=5, decimal_places=2)
    cureHours = serializers.DecimalField(
        source="cure_hours",
        max_digits=6,
        decimal_places=2,
        required=False,
        allow_null=True,
    )
    rollCode = serializers.CharField(source="roll.roll_code", read_only=True)
    loftName = serializers.CharField(source="roll.loft.name", read_only=True)

    class Meta:
        model = DipRun
        fields = (
            "id",
            "rollId",
            "rollCode",
            "loftName",
            "startedAt",
            "resinPct",
            "cureHours",
            "notes",
            "created_at",
        )
        read_only_fields = ("id", "rollCode", "loftName", "created_at")


class SaltSprayCouponSerializer(serializers.ModelSerializer):
    rollId = serializers.PrimaryKeyRelatedField(
        source="roll", queryset=ClothRoll.objects.all()
    )
    stripNo = serializers.IntegerField(source="strip_no", min_value=1)
    blisterGrade = serializers.IntegerField(source="blister_grade", min_value=0, max_value=5)
    inspectedAt = serializers.DateTimeField(source="inspected_at")
    inspectorId = serializers.IntegerField(source="inspector_id", read_only=True)
    inspectorName = serializers.CharField(source="inspector.username", read_only=True)
    voidedAt = serializers.DateTimeField(source="voided_at", read_only=True)
    rollCode = serializers.CharField(source="roll.roll_code", read_only=True)
    loftName = serializers.CharField(source="roll.loft.name", read_only=True)

    class Meta:
        model = SaltSprayCoupon
        fields = (
            "id",
            "rollId",
            "rollCode",
            "loftName",
            "stripNo",
            "blisterGrade",
            "inspectedAt",
            "inspectorId",
            "inspectorName",
            "voidedAt",
            "created_at",
        )
        read_only_fields = (
            "id",
            "inspectorId",
            "inspectorName",
            "voidedAt",
            "rollCode",
            "loftName",
            "created_at",
        )

    def validate(self, attrs):
        # 新建时校验；并发抢同号的情况由数据库部分唯一约束兜底。
        if self.instance is None:
            roll = attrs.get("roll")
            strip_no = attrs.get("strip_no")
            if roll is not None and strip_no is not None:
                if SaltSprayCoupon.objects.filter(
                    roll=roll, strip_no=strip_no, voided_at__isnull=True
                ).exists():
                    raise serializers.ValidationError(
                        {"stripNo": "该布卷已有同条号的未作废盐雾试片条"}
                    )
        return attrs

