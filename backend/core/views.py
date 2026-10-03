from django.db import IntegrityError
from django.db.models import Count
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import ClothRoll, DipRun, Loft, SaltSprayCoupon
from .serializers import (
    ClothRollSerializer,
    DipRunSerializer,
    LoftSerializer,
    SaltSprayCouponSerializer,
)


class LoftViewSet(viewsets.ModelViewSet):
    queryset = Loft.objects.annotate(roll_count=Count("rolls")).all()
    serializer_class = LoftSerializer


class ClothRollViewSet(viewsets.ModelViewSet):
    serializer_class = ClothRollSerializer

    def get_queryset(self):
        qs = ClothRoll.objects.select_related("loft").all()
        loft_id = self.request.query_params.get("loftId")
        status_param = self.request.query_params.get("status")
        if loft_id:
            qs = qs.filter(loft_id=loft_id)
        if status_param:
            qs = qs.filter(status=status_param)
        return qs


class DipRunViewSet(viewsets.ModelViewSet):
    serializer_class = DipRunSerializer
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        qs = DipRun.objects.select_related("roll", "roll__loft").all()
        roll_id = self.request.query_params.get("rollId")
        if roll_id:
            qs = qs.filter(roll_id=roll_id)
        return qs


class SaltSprayCouponViewSet(viewsets.ModelViewSet):
    serializer_class = SaltSprayCouponSerializer
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        qs = SaltSprayCoupon.objects.select_related(
            "roll", "roll__loft", "inspector"
        ).all()
        roll_id = self.request.query_params.get("rollId")
        if roll_id:
            qs = qs.filter(roll_id=roll_id)
        return qs

    def perform_create(self, serializer):
        # 两名质检抢同一卷同一条号时，数据库部分唯一约束只放一张落库。
        try:
            serializer.save(inspector=self.request.user)
        except IntegrityError:
            raise ValidationError(
                {"stripNo": "该布卷已有同条号的未作废盐雾试片条，落库被拒绝"}
            )

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="void",
    )
    def void(self, request, pk=None):
        # 作废仅管理员。
        if request.user.role != "admin":
            return Response(
                {"detail": "只有管理员可以作废盐雾试片条"},
                status=status.HTTP_403_FORBIDDEN,
            )
        coupon = self.get_object()
        if coupon.voided_at is not None:
            return Response(
                {"detail": "该盐雾试片条已作废，不能重复作废"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        coupon.voided_at = timezone.now()
        coupon.save(update_fields=["voided_at"])
        return Response(self.get_serializer(coupon).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    data = {
        "loftCount": Loft.objects.count(),
        "rawRollCount": ClothRoll.objects.filter(status=ClothRoll.STATUS_RAW).count(),
        "dippingRollCount": ClothRoll.objects.filter(
            status=ClothRoll.STATUS_DIPPING
        ).count(),
        "curedRollCount": ClothRoll.objects.filter(status=ClothRoll.STATUS_CURED).count(),
        "dipRunCount": DipRun.objects.count(),
    }
    return Response(data)
