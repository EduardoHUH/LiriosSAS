import stripe
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from payments.services import construct_event, process_event


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Receives Stripe webhook events. Not a DRF view: signature
    verification needs the exact raw request body, and this endpoint is
    authenticated by that signature rather than by session/JWT/CSRF -- so
    it's exempted from CSRF the same way any server-to-server webhook is."""

    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    try:
        event = construct_event(request.body, sig_header)
    except (ValueError, stripe.SignatureVerificationError):
        return HttpResponse(status=400)

    process_event(event)
    return HttpResponse(status=200)
