from django.db.models import ProtectedError
from rest_framework import status
from rest_framework.response import Response


class ProtectedDeleteMixin:
    """Turns a PROTECT-related IntegrityError into a clean 409 instead of
    an unhandled 500 when deleting a row still referenced elsewhere."""

    protected_delete_message = "No se puede eliminar este elemento porque está en uso."

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"detail": self.protected_delete_message},
                status=status.HTTP_409_CONFLICT,
            )
