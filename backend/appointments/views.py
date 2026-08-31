from datetime import date

import stripe
from rest_framework import generics, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

from appointments.models import Appointment, AppointmentStatus
from appointments.serializers import (
    AppointmentAdminSerializer,
    AppointmentCancelRequestSerializer,
    AppointmentCreateSerializer,
    AppointmentCustomerSerializer,
    AppointmentRescheduleRequestSerializer,
)
from appointments.services import (
    CancellationPolicyError,
    InvalidTransitionError,
    ReschedulePolicyError,
    SlotNotAvailableError,
    cancel_appointment,
    reschedule_appointment,
    transition_appointment,
)
from payments.services import PaymentError, create_checkout_session, refund_if_paid


class AppointmentCreateView(generics.CreateAPIView):
    serializer_class = AppointmentCreateSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            appointment = serializer.save()
        except SlotNotAvailableError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(
            AppointmentCustomerSerializer(appointment).data, status=status.HTTP_201_CREATED
        )


class AppointmentTokenViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Passwordless customer access to a single appointment via its
    unguessable access_token -- there are no customer accounts."""

    serializer_class = AppointmentCustomerSerializer
    permission_classes = [AllowAny]
    queryset = Appointment.objects.select_related("service", "service__category")
    lookup_field = "access_token"
    lookup_url_kwarg = "token"

    @action(detail=True, methods=["post"])
    def cancel(self, request, token=None):
        appointment = self.get_object()
        input_serializer = AppointmentCancelRequestSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        try:
            cancel_appointment(appointment, reason=input_serializer.validated_data["reason"])
        except (CancellationPolicyError, InvalidTransitionError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        refund_if_paid(appointment)
        return Response(AppointmentCustomerSerializer(appointment).data)

    @action(detail=True, methods=["post"])
    def pay(self, request, token=None):
        appointment = self.get_object()
        try:
            checkout_url = create_checkout_session(appointment)
        except PaymentError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except stripe.StripeError:
            return Response(
                {"detail": "No se pudo iniciar el pago en este momento. Intenta de nuevo más tarde."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response({"checkout_url": checkout_url})

    @action(detail=True, methods=["post"])
    def reschedule(self, request, token=None):
        appointment = self.get_object()
        input_serializer = AppointmentRescheduleRequestSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        try:
            reschedule_appointment(
                appointment, input_serializer.validated_data["start_datetime"]
            )
        except (ReschedulePolicyError, InvalidTransitionError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except SlotNotAvailableError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(AppointmentCustomerSerializer(appointment).data)


class AppointmentAdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        if self.action == "create":
            return AppointmentCreateSerializer
        return AppointmentAdminSerializer

    def get_queryset(self):
        queryset = Appointment.objects.select_related("service", "customer").all()
        params = self.request.query_params

        status_param = params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param)

        service_id = params.get("service")
        if service_id and service_id.isdigit():
            queryset = queryset.filter(service_id=service_id)

        email = params.get("customer_email")
        if email:
            queryset = queryset.filter(customer__email__icontains=email)

        date_from = params.get("date_from")
        if date_from:
            try:
                queryset = queryset.filter(start_datetime__date__gte=date.fromisoformat(date_from))
            except ValueError:
                pass

        date_to = params.get("date_to")
        if date_to:
            try:
                queryset = queryset.filter(start_datetime__date__lte=date.fromisoformat(date_to))
            except ValueError:
                pass

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            appointment = serializer.save()
        except SlotNotAvailableError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(
            AppointmentAdminSerializer(appointment).data, status=status.HTTP_201_CREATED
        )

    def destroy(self, request, *args, **kwargs):
        return Response(
            {"detail": "Las citas no se eliminan; usa la acción 'cancel'."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        appointment = self.get_object()
        try:
            transition_appointment(appointment, AppointmentStatus.CONFIRMED)
        except InvalidTransitionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(AppointmentAdminSerializer(appointment).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        appointment = self.get_object()
        input_serializer = AppointmentCancelRequestSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        try:
            cancel_appointment(
                appointment,
                reason=input_serializer.validated_data["reason"],
                enforce_deadline=False,
            )
        except InvalidTransitionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        refund_if_paid(appointment)
        return Response(AppointmentAdminSerializer(appointment).data)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        appointment = self.get_object()
        try:
            transition_appointment(appointment, AppointmentStatus.COMPLETED)
        except InvalidTransitionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(AppointmentAdminSerializer(appointment).data)

    @action(detail=True, methods=["post"], url_path="no-show")
    def no_show(self, request, pk=None):
        appointment = self.get_object()
        try:
            transition_appointment(appointment, AppointmentStatus.NO_SHOW)
        except InvalidTransitionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(AppointmentAdminSerializer(appointment).data)

    @action(detail=True, methods=["post"])
    def reschedule(self, request, pk=None):
        appointment = self.get_object()
        input_serializer = AppointmentRescheduleRequestSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        try:
            reschedule_appointment(
                appointment,
                input_serializer.validated_data["start_datetime"],
                enforce_policy=False,
            )
        except InvalidTransitionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except SlotNotAvailableError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(AppointmentAdminSerializer(appointment).data)
