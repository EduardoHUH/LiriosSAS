from rest_framework.exceptions import Throttled
from rest_framework.views import exception_handler


def spanish_throttle_exception_handler(exc, context):
    """Wraps DRF's default exception handler to translate the one
    English-only error message DRF raises itself (Throttled) -- every other
    user-facing error in this codebase is Spanish."""

    response = exception_handler(exc, context)
    if response is not None and isinstance(exc, Throttled):
        if exc.wait is not None:
            detail = (
                f"Demasiadas solicitudes. Intenta de nuevo en {int(exc.wait)} segundos."
            )
        else:
            detail = "Demasiadas solicitudes. Intenta de nuevo más tarde."
        response.data = {"detail": detail}
    return response
