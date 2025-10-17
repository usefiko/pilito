"""
Intercom Webhooks Handler
Handles incoming webhooks from Intercom for two-way sync of tickets
"""

import hashlib
import hmac
import json
import logging
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)


def verify_webhook_signature(request):
    """
    Verify Intercom webhook signature for security.
    
    Intercom sends X-Hub-Signature header with HMAC-SHA256 hash.
    Docs: https://developers.intercom.com/docs/references/webhooks/securing-webhooks
    
    Args:
        request: Django request object
        
    Returns:
        bool: True if signature is valid, False otherwise
    """
    signature = request.headers.get('X-Hub-Signature')
    if not signature:
        logger.warning("⚠️ Webhook received without X-Hub-Signature header")
        return False
    
    # Get webhook secret from settings
    webhook_secret = getattr(settings, 'INTERCOM_WEBHOOK_SECRET', None)
    if not webhook_secret:
        logger.error("❌ INTERCOM_WEBHOOK_SECRET not configured in settings")
        return False
    
    # Calculate expected signature
    # Note: Intercom uses SHA-1, not SHA-256!
    secret_bytes = webhook_secret.encode('utf-8')
    body_bytes = request.body
    
    expected_signature = hmac.new(
        secret_bytes,
        body_bytes,
        hashlib.sha1  # ⚠️ SHA-1, not SHA-256
    ).hexdigest()
    
    # Remove "sha1=" prefix from signature if present
    if signature.startswith('sha1='):
        signature = signature[5:]
    
    # Compare signatures (constant-time comparison to prevent timing attacks)
    if not hmac.compare_digest(expected_signature, signature):
        logger.error(
            f"❌ Invalid webhook signature. "
            f"Expected: {expected_signature[:10]}..., Got: {signature[:10]}..."
        )
        return False
    
    logger.debug("✅ Webhook signature verified successfully")
    return True


@csrf_exempt
@require_POST
def intercom_webhook_handler(request):
    """
    Main webhook handler for Intercom events.
    
    Handles the following topics for two-way ticket sync:
    - ticket.admin.replied: Support agent replied to ticket → sync to Fiko
    - ticket.contact.replied: Customer replied to ticket
    - ticket.state_updated: Ticket status/state changed → sync to Fiko
    - ticket.closed: Ticket was closed → update status in Fiko
    
    Endpoint URL to configure in Intercom:
    https://api.pilito.com/api/webhooks/intercom/
    
    Args:
        request: Django POST request with webhook data
        
    Returns:
        JsonResponse with status and result
    """
    
    # 1. Verify webhook signature for security
    if not verify_webhook_signature(request):
        logger.error("❌ Webhook signature verification failed - possible security issue")
        return JsonResponse(
            {"error": "Invalid signature"},
            status=401
        )
    
    # 2. Parse webhook payload
    try:
        payload = json.loads(request.body.decode('utf-8'))
        topic = payload.get("topic")
        data = payload.get("data", {})
        item = data.get("item", {})
        
        logger.info(f"📥 Received Intercom webhook: {topic}")
        logger.debug(f"Webhook payload: {json.dumps(payload, indent=2)}")
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Invalid JSON in webhook body: {str(e)}")
        return JsonResponse(
            {"error": "Invalid JSON"},
            status=400
        )
    except Exception as e:
        logger.error(f"❌ Error parsing webhook: {str(e)}")
        return JsonResponse(
            {"error": "Parse error"},
            status=400
        )
    
    # 3. Route to appropriate handler based on topic
    try:
        if topic == "ticket.admin.replied":
            return handle_ticket_admin_replied(item)
        
        elif topic == "ticket.contact.replied":
            return handle_ticket_contact_replied(item)
        
        elif topic == "ticket.state_updated":
            return handle_ticket_state_updated(item)
        
        elif topic == "ticket.closed":
            return handle_ticket_closed(item)
        
        else:
            logger.warning(f"⚠️ Unhandled webhook topic: {topic}")
            return JsonResponse(
                {"status": "ignored", "topic": topic},
                status=200
            )
            
    except Exception as e:
        logger.error(f"❌ Error handling webhook {topic}: {str(e)}")
        return JsonResponse(
            {"error": str(e)},
            status=500
        )


def handle_ticket_admin_replied(ticket_data: dict) -> JsonResponse:
    """
    Handle ticket.admin.replied webhook.
    
    This webhook is triggered when a support agent replies to a ticket in Intercom.
    We need to sync this reply back to Fiko as a SupportMessage.
    
    Args:
        ticket_data: Intercom ticket data from webhook
        
    Returns:
        JsonResponse with sync result
    """
    from settings.models import SupportTicket, SupportMessage
    
    try:
        intercom_ticket_id = ticket_data.get("id")
        
        if not intercom_ticket_id:
            logger.error("❌ No ticket ID in webhook data")
            return JsonResponse({"error": "Missing ticket ID"}, status=400)
        
        # Find Fiko ticket by Intercom ticket ID
        try:
            fiko_ticket = SupportTicket.objects.get(intercom_ticket_id=intercom_ticket_id)
        except SupportTicket.DoesNotExist:
            logger.error(f"❌ Fiko ticket not found for Intercom ticket {intercom_ticket_id}")
            return JsonResponse(
                {"error": "Ticket not found"},
                status=404
            )
        
        # Extract reply data from webhook
        # Note: Structure may vary by webhook version - adjust as needed
        conversation_parts = ticket_data.get("conversation_parts", {}).get("conversation_parts", [])
        
        if not conversation_parts:
            # Try alternative structure
            body = ticket_data.get("body", "")
            author = ticket_data.get("author", {})
            admin_name = author.get("name", "Support Team")
        else:
            # Get latest reply
            latest_part = conversation_parts[-1]
            author = latest_part.get("author", {})
            admin_name = author.get("name", "Support Team")
            body = latest_part.get("body", "")
        
        if not body:
            logger.warning(f"⚠️ No message body in admin reply for ticket {intercom_ticket_id}")
            return JsonResponse(
                {"status": "no_content"},
                status=200
            )
        
        # Create SupportMessage in Fiko
        support_message = SupportMessage.objects.create(
            ticket=fiko_ticket,
            content=body,
            sender=None,  # Admin message, not from a User
            is_from_support=True
        )
        
        logger.info(
            f"✅ Synced admin reply from Intercom ticket {intercom_ticket_id} "
            f"to Fiko ticket #{fiko_ticket.id} as message #{support_message.id}"
        )
        
        # TODO: Send WebSocket notification to frontend
        # from message.utils import send_websocket_notification
        # send_websocket_notification(...)
        
        return JsonResponse({
            "status": "synced",
            "fiko_ticket_id": fiko_ticket.id,
            "message_id": support_message.id
        }, status=200)
        
    except Exception as e:
        logger.error(f"❌ Error handling admin reply: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


def handle_ticket_contact_replied(ticket_data: dict) -> JsonResponse:
    """
    Handle ticket.contact.replied webhook.
    
    This webhook is triggered when a customer replies to a ticket in Intercom.
    Usually not needed since customer replies originate from Fiko, but we handle
    it for completeness (e.g., if customer replies directly in Intercom).
    
    Args:
        ticket_data: Intercom ticket data from webhook
        
    Returns:
        JsonResponse with result
    """
    logger.info("📝 Contact reply webhook received (usually no action needed)")
    
    # If you want to sync customer replies from Intercom to Fiko:
    # Implement similar logic to handle_ticket_admin_replied but with is_from_support=False
    
    return JsonResponse({
        "status": "acknowledged"
    }, status=200)


def handle_ticket_state_updated(ticket_data: dict) -> JsonResponse:
    """
    Handle ticket.state_updated webhook.
    
    This webhook is triggered when a ticket's state changes in Intercom.
    We sync the state change back to Fiko's SupportTicket.
    
    Args:
        ticket_data: Intercom ticket data from webhook
        
    Returns:
        JsonResponse with sync result
    """
    from settings.models import SupportTicket
    
    try:
        intercom_ticket_id = ticket_data.get("id")
        new_state = ticket_data.get("state")
        
        if not intercom_ticket_id:
            logger.error("❌ No ticket ID in webhook data")
            return JsonResponse({"error": "Missing ticket ID"}, status=400)
        
        if not new_state:
            logger.warning("⚠️ No state in webhook data")
            return JsonResponse({"status": "no_state"}, status=200)
        
        # Find Fiko ticket
        try:
            fiko_ticket = SupportTicket.objects.get(intercom_ticket_id=intercom_ticket_id)
        except SupportTicket.DoesNotExist:
            logger.error(f"❌ Fiko ticket not found for Intercom ticket {intercom_ticket_id}")
            return JsonResponse(
                {"error": "Ticket not found"},
                status=404
            )
        
        # Map Intercom state to Fiko status
        state_mapping = {
            'submitted': 'open',
            'in_progress': 'under_review',
            'waiting_on_customer': 'support_response',
            'resolved': 'closed',
        }
        
        fiko_status = state_mapping.get(new_state)
        
        if not fiko_status:
            logger.warning(f"⚠️ Unknown Intercom state: {new_state}")
            return JsonResponse(
                {"status": "unknown_state", "state": new_state},
                status=200
            )
        
        # Update Fiko ticket status if different
        if fiko_ticket.status != fiko_status:
            old_status = fiko_ticket.status
            fiko_ticket.status = fiko_status
            fiko_ticket.save(update_fields=['status', 'updated_at'])
            
            logger.info(
                f"✅ Updated Fiko ticket #{fiko_ticket.id} status: "
                f"{old_status} → {fiko_status} (Intercom state: {new_state})"
            )
            
            return JsonResponse({
                "status": "synced",
                "fiko_ticket_id": fiko_ticket.id,
                "old_status": old_status,
                "new_status": fiko_status
            }, status=200)
        else:
            logger.info(f"ℹ️ Fiko ticket #{fiko_ticket.id} status already {fiko_status}")
            return JsonResponse({
                "status": "no_change",
                "fiko_ticket_id": fiko_ticket.id
            }, status=200)
        
    except Exception as e:
        logger.error(f"❌ Error handling state update: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


def handle_ticket_closed(ticket_data: dict) -> JsonResponse:
    """
    Handle ticket.closed webhook.
    
    This webhook is triggered when a ticket is closed in Intercom.
    We mark the corresponding Fiko ticket as closed.
    
    Args:
        ticket_data: Intercom ticket data from webhook
        
    Returns:
        JsonResponse with sync result
    """
    from settings.models import SupportTicket
    
    try:
        intercom_ticket_id = ticket_data.get("id")
        
        if not intercom_ticket_id:
            logger.error("❌ No ticket ID in webhook data")
            return JsonResponse({"error": "Missing ticket ID"}, status=400)
        
        # Find Fiko ticket
        try:
            fiko_ticket = SupportTicket.objects.get(intercom_ticket_id=intercom_ticket_id)
        except SupportTicket.DoesNotExist:
            logger.error(f"❌ Fiko ticket not found for Intercom ticket {intercom_ticket_id}")
            return JsonResponse(
                {"error": "Ticket not found"},
                status=404
            )
        
        # Close ticket if not already closed
        if fiko_ticket.status != 'closed':
            old_status = fiko_ticket.status
            fiko_ticket.status = 'closed'
            fiko_ticket.save(update_fields=['status', 'updated_at'])
            
            logger.info(
                f"✅ Closed Fiko ticket #{fiko_ticket.id} (was: {old_status}) "
                f"via Intercom webhook"
            )
            
            return JsonResponse({
                "status": "closed",
                "fiko_ticket_id": fiko_ticket.id,
                "old_status": old_status
            }, status=200)
        else:
            logger.info(f"ℹ️ Fiko ticket #{fiko_ticket.id} already closed")
            return JsonResponse({
                "status": "already_closed",
                "fiko_ticket_id": fiko_ticket.id
            }, status=200)
        
    except Exception as e:
        logger.error(f"❌ Error handling ticket close: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)

