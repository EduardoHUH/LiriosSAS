from django.db.models import Count, Q
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.mixins import ProtectedDeleteMixin
from customers.models import Customer
from customers.serializers import CustomerAdminSerializer


class CustomerAdminViewSet(ProtectedDeleteMixin, ModelViewSet):
    serializer_class = CustomerAdminSerializer
    permission_classes = [IsAdminUser]
    protected_delete_message = (
        "No se puede eliminar este cliente porque tiene citas asociadas."
    )

    def get_queryset(self):
        queryset = Customer.objects.annotate(appointment_count=Count("appointments"))
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search)
                | Q(email__icontains=search)
                | Q(phone__icontains=search)
            )
        return queryset

    @action(detail=True, methods=["get"])
    def appointments(self, request, pk=None):
        # Imported lazily to avoid a module-level dependency from
        # customers on appointments (appointments already depends on
        # customers the other way, at the model level).
        from appointments.serializers import AppointmentAdminSerializer

        customer = self.get_object()
        queryset = customer.appointments.select_related("service").order_by("-start_datetime")
        return Response(AppointmentAdminSerializer(queryset, many=True).data)
