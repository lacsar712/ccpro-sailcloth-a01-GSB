from django.db import IntegrityError
from django.db.models import Count
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import User

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
        status = self.request.query_params.get("status")
        if loft_id:
            qs = qs.filter(loft_id=loft_id)
        if status:
            qs = qs.filter(status=status)
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
    """盐雾试片条：操作工可建条；作废仅管理员。"""

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
        try:
            serializer.save(inspector=self.request.user)
        except IntegrityError:
            # 两名质检同时交同一条号：数据库部分唯一约束只放行一张
            raise ValidationError({"couponNo": "该布卷已存在未作废的同号盐雾试片条"})

    @action(detail=True, methods=["post"])
    def void(self, request, pk=None):
        if request.user.role != User.ROLE_ADMIN:
            raise PermissionDenied("仅管理员可作废盐雾试片条")
        coupon = self.get_object()
        if coupon.voided_at is not None:
            raise ValidationError({"detail": "该盐雾试片条已作废"})
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
