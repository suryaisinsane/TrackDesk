"""Verify that /webhooks/email requests really come from Resend.

Resend signs webhooks with Svix. Each request carries three headers:
svix-id, svix-timestamp, svix-signature. We recompute the HMAC of
"{id}.{timestamp}.{raw_body}" with your signing secret and compare.

Set RESEND_WEBHOOK_SECRET (starts with "whsec_") from the Resend
dashboard -> Webhooks -> your endpoint -> Signing secret.
"""
import base64
import hashlib
import hmac
import json
import os
import time

from fastapi import HTTPException, Request

TOLERANCE_SECONDS = 5 * 60


def _verify(secret: str, msg_id: str, timestamp: str, signature_header: str, body: bytes) -> bool:
    try:
        ts = int(timestamp)
    except ValueError:
        return False

    # Reject old or far-future requests (replay protection)
    if abs(time.time() - ts) > TOLERANCE_SECONDS:
        return False

    key = base64.b64decode(secret.removeprefix("whsec_"))
    signed = f"{msg_id}.{timestamp}.".encode() + body
    expected = base64.b64encode(hmac.new(key, signed, hashlib.sha256).digest()).decode()

    # Header looks like "v1,<sig> v1,<sig2>"
    for part in signature_header.split():
        version, _, sig = part.partition(",")
        if version == "v1" and hmac.compare_digest(sig, expected):
            return True
    return False


async def verify_resend_webhook(request: Request) -> dict:
    secret = os.getenv("RESEND_WEBHOOK_SECRET")
    if not secret:
        # Fail closed: never accept unsigned webhooks
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    body = await request.body()
    msg_id = request.headers.get("svix-id", "")
    timestamp = request.headers.get("svix-timestamp", "")
    signature = request.headers.get("svix-signature", "")

    if not (msg_id and timestamp and signature) or not _verify(
        secret, msg_id, timestamp, signature, body
    ):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        return json.loads(body)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid JSON")