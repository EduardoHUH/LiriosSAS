from django.core.exceptions import ValidationError
from PIL import Image

MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}


def validate_image_file(value):
    """Rejects oversized uploads and anything that isn't actually one of
    our allowed image formats. Checks the real decoded format rather than
    trusting the filename extension or client-supplied content type."""

    if value.size > MAX_IMAGE_SIZE_BYTES:
        raise ValidationError("La imagen no debe superar los 5 MB.")

    value.seek(0)
    try:
        image = Image.open(value)
        image_format = image.format
    except Exception as exc:
        raise ValidationError("El archivo no es una imagen válida.") from exc
    finally:
        value.seek(0)

    if image_format not in ALLOWED_IMAGE_FORMATS:
        raise ValidationError("Formato de imagen no permitido. Usa JPEG, PNG o WEBP.")
