"""
Zarinpal Payment Gateway Integration for Pilito Billing System

This module contains payment APIs for both legacy and modern billing systems:

LEGACY APIs (using Purchases model):
- Payment: Legacy payment API using Purchases model
- PaymentVerify: Legacy verification API using Purchases model

NEW APIs (using modern billing system with TokenPlan/FullPlan/Subscription):
- ZPPayment: Initiates Zarinpal payment for TokenPlan or FullPlan
  POST /billing/zp-pay
  Body: {
    "token_plan_id": 1,  // OR "full_plan_id": 2
  }
  Returns: {payment_id, authority, url} - Redirect user to url

- ZPVerify: Verifies Zarinpal payment and creates/updates subscription
  GET /billing/zp-verify/{payment_id}/?Authority=xxx&Status=OK
  Automatically called by Zarinpal after payment
  Creates or updates user subscription based on purchased plan
  
SUBSCRIPTION LOGIC:
- If user has no subscription or inactive subscription: Creates new subscription
- If user has active subscription: Queues the new plan for activation after current plan expires
- TokenPlan: Adds tokens without expiration date
- FullPlan: Adds tokens with expiration based on duration_days
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
import json
import requests
from django.conf import settings
from core.responses import bad_request, SuccessResponse, UnsuccessfulResponse
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.shortcuts import redirect
from django.utils import timezone
from datetime import timedelta
from billing.models import TokenPlan, FullPlan, Subscription, Payment as PaymentModel, Purchases
from billing.serializers import PurchasesSerializer, ZarinpalPaymentSerializer, PaymentSerializer



class Payment(APIView):
    serializer_class = PurchasesSerializer  
    permission_classes = [IsAuthenticated]

    def post(self, *args, **kwargs):
        authority = self.request.query_params.get("Authority")
        status = self.request.query_params.get("Status")
        data = self.request.data
        data["user"] = self.request.user.id
        data["description"] = "خرید اشتراک پیلیتو"

        serializer = self.serializer_class(data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            purchase = Purchases.objects.get(id=serializer.data['id'])  

            data = {
                "MerchantID": settings.ZARRINPAL_MERCHANT_ID,  # betterme zarinpal merchent
                "Amount": purchase.price,  
                "Description": purchase.description,
                "Authority": authority,
                "Phone": str(self.request.user.phone_number),
                "CallbackURL": settings.ZARIN_CALL_BACK + str(purchase.id) + "/",
                "PurchasesID": purchase.id,
            }
            data = json.dumps(data)
            headers = {'content-type': 'application/json', 'content-length': str(len(data))}

            try:
                response = requests.post(settings.ZP_API_REQUEST, data=data, headers=headers, timeout=10)
                response.raise_for_status()

                if response.status_code == 200:
                    response = response.json()
                    print('---------------')
                    print(response)
                    if response['Status'] == 100:
                        purchase.authority = response['Authority']
                        purchase.save()
                        purchase_serializer = self.serializer_class(purchase)
                        data = {'status': True, 'url': settings.ZP_API_STARTPAY + str(response['Authority']),
                                'purchase': purchase.id, 'authority': response['Authority']}
                        return SuccessResponse(purchase_serializer.data, data)
                    else:
                        return Response(response['errors'], status=400)
                        # return {'status': False, 'code': str(response['Status'])}
                return response

            except requests.exceptions.Timeout:
                return {'status': False, 'code': 'timeout'}
            except requests.exceptions.ConnectionError:
                return {'status': False, 'code': 'connection error'}

        return Response(serializer.errors, status=status.HTTP_406_NOT_ACCEPTABLE)




class PaymentVerify(APIView):
    serializer_class = PurchasesSerializer
    permission_classes = [AllowAny]

    @transaction.atomic
    def get(self, *args, **kwargs):
        status = self.request.query_params.get("Status")
        authority = self.request.query_params.get("Authority")
        id = self.kwargs.get("id")

        if not authority or status != "OK":
            return redirect('https://app.pilito.com/dashboard/payment/failure')

        try:
            purchase = Purchases.objects.get(id=id)
        except Purchases.DoesNotExist:
            return bad_request("purchase does not exist...")

        data = {
            "MerchantID": settings.ZARRINPAL_MERCHANT_ID,
            "Amount": purchase.price,
            "Authority": authority,
        }
        #data = json.dumps(data)
        data = json.dumps(data).encode('utf-8')

        headers = {'content-type': 'application/json', 'content-length': str(len(data))}
        response = requests.post(settings.ZP_API_VERIFY, data=data, headers=headers)

        if response.status_code == 200:
            response = response.json()
            #if response['Status'] == 100:
            if response.get('Status') == 100:
                purchase.paid = True
                purchase.authority = authority
                purchase.ref_id = response['RefID']
                purchase.save()

                return redirect(f'https://app.pilito.com/dashboard/payment/success?payment_id={response["RefID"]}')
            else:
                return SuccessResponse(data={'status': False, 'details': 'purchase already paid' })
        return SuccessResponse(data=response.content)


# ==================== NEW ZARINPAL APIs FOR MODERN BILLING SYSTEM ====================

class ZPPayment(APIView):
    """
    Zarinpal Payment API for new billing system
    Initiates payment with TokenPlan or FullPlan
    """
    serializer_class = ZarinpalPaymentSerializer
    permission_classes = [IsAuthenticated]

    def post(self, *args, **kwargs):
        serializer = self.serializer_class(data=self.request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        plan = validated_data['plan']
        plan_type = validated_data['plan_type']

        # Get the price from the plan
        amount = plan.price
        
        # Convert to Rials (Zarinpal uses Rials, multiply by 10 if you're storing in Toman)
        # Assuming amount is in Toman, convert to Rials
        amount_rials = int(float(amount) * 10)

        # Create Payment record
        payment = PaymentModel.objects.create(
            user=self.request.user,
            token_plan=plan if plan_type == 'token' else None,
            full_plan=plan if plan_type == 'full' else None,
            amount=amount,
            payment_method='other',  # Can add 'zarinpal' to PAYMENT_METHOD_CHOICES
            status='pending',
            payment_gateway_response={}
        )

        # Prepare Zarinpal request
        description = f"خرید اشتراک {plan.name} - Pilito"
        callback_url = settings.ZARIN_CALL_BACK.replace('/payment-verify/', f'/zp-verify/{payment.id}/')
        
        zarinpal_data = {
            "MerchantID": settings.ZARRINPAL_MERCHANT_ID,
            "Amount": amount_rials,
            "Description": description,
            "Phone": str(self.request.user.phone_number) if hasattr(self.request.user, 'phone_number') else "",
            "CallbackURL": callback_url,
        }

        headers = {
            'content-type': 'application/json',
            'content-length': str(len(json.dumps(zarinpal_data)))
        }

        try:
            response = requests.post(
                settings.ZP_API_REQUEST, 
                data=json.dumps(zarinpal_data), 
                headers=headers, 
                timeout=10
            )
            response.raise_for_status()

            if response.status_code == 200:
                response_data = response.json()
                
                if response_data.get('Status') == 100:
                    # Update payment with authority
                    payment.authority = response_data['Authority']
                    payment.save()

                    payment_url = settings.ZP_API_STARTPAY + str(response_data['Authority'])
                    
                    return SuccessResponse(
                        PaymentSerializer(payment).data,
                        {
                            'status': True,
                            'url': payment_url,
                            'payment_id': payment.id,
                            'authority': response_data['Authority']
                        }
                    )
                else:
                    payment.status = 'failed'
                    payment.payment_gateway_response = response_data
                    payment.save()
                    return Response(
                        {'error': 'Zarinpal error', 'details': response_data},
                        status=status.HTTP_400_BAD_REQUEST
                    )

        except requests.exceptions.Timeout:
            payment.status = 'failed'
            payment.save()
            return Response(
                {'error': 'Gateway timeout'},
                status=status.HTTP_408_REQUEST_TIMEOUT
            )
        except requests.exceptions.RequestException as e:
            payment.status = 'failed'
            payment.save()
            return Response(
                {'error': 'Connection error', 'details': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


class ZPVerify(APIView):
    """
    Zarinpal Verification API for new billing system
    Verifies payment and creates/updates subscription
    """
    permission_classes = [AllowAny]

    @transaction.atomic
    def get(self, *args, **kwargs):
        payment_status = self.request.query_params.get("Status")
        authority = self.request.query_params.get("Authority")
        payment_id = self.kwargs.get("id")

        # Check if payment was cancelled by user
        if not authority or payment_status != "OK":
            try:
                payment = PaymentModel.objects.get(id=payment_id)
                payment.status = 'cancelled'
                payment.save()
            except PaymentModel.DoesNotExist:
                pass
            return redirect('https://app.pilito.com/dashboard/payment/failure')

        # Get payment record
        try:
            payment = PaymentModel.objects.select_for_update().get(id=payment_id)
        except PaymentModel.DoesNotExist:
            return redirect('https://app.pilito.com/dashboard/payment/failure?error=payment_not_found')

        # Check if already verified
        if payment.status == 'completed':
            return redirect(f'https://app.pilito.com/dashboard/payment/success?payment_id={payment.ref_id}')

        # Verify with Zarinpal
        amount_rials = int(float(payment.amount) * 10)
        verify_data = {
            "MerchantID": settings.ZARRINPAL_MERCHANT_ID,
            "Amount": amount_rials,
            "Authority": authority,
        }

        headers = {
            'content-type': 'application/json',
            'content-length': str(len(json.dumps(verify_data)))
        }

        try:
            response = requests.post(
                settings.ZP_API_VERIFY, 
                data=json.dumps(verify_data).encode('utf-8'), 
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                response_data = response.json()
                
                # Payment verified successfully
                if response_data.get('Status') == 100:
                    # Update payment record
                    payment.status = 'completed'
                    payment.authority = authority
                    payment.ref_id = str(response_data.get('RefID', ''))
                    payment.transaction_id = str(response_data.get('RefID', ''))
                    payment.payment_date = timezone.now()
                    payment.payment_gateway_response = response_data
                    payment.save()

                    # Create or update subscription
                    self._process_subscription(payment)

                    return redirect(f'https://app.pilito.com/dashboard/payment/success?payment_id={payment.ref_id}')
                
                # Payment verification failed
                else:
                    payment.status = 'failed'
                    payment.payment_gateway_response = response_data
                    payment.save()
                    return redirect(f'https://app.pilito.com/dashboard/payment/failure?error=verification_failed&code={response_data.get("Status")}')
            
            else:
                payment.status = 'failed'
                payment.save()
                return redirect('https://app.pilito.com/dashboard/payment/failure?error=gateway_error')

        except requests.exceptions.RequestException as e:
            payment.status = 'failed'
            payment.save()
            return redirect('https://app.pilito.com/dashboard/payment/failure?error=connection_error')

    def _process_subscription(self, payment):
        """
        Process subscription after successful payment
        Creates new subscription or updates existing one
        """
        user = payment.user
        
        # Get or create subscription
        try:
            subscription = Subscription.objects.get(user=user)
            has_existing_subscription = True
        except Subscription.DoesNotExist:
            subscription = Subscription(user=user)
            has_existing_subscription = False

        # Determine plan type and details
        if payment.token_plan:
            plan = payment.token_plan
            tokens = plan.tokens_included
            duration_days = None
            plan_type = 'token'
        elif payment.full_plan:
            plan = payment.full_plan
            tokens = plan.tokens_included
            duration_days = plan.duration_days
            plan_type = 'full'
        else:
            return  # No plan associated, shouldn't happen

        # Handle existing active subscription
        if has_existing_subscription and subscription.is_subscription_active():
            # If user has active subscription, queue the new plan
            if plan_type == 'token':
                subscription.queued_token_plan = plan
                subscription.queued_tokens_amount = tokens
            else:
                subscription.queued_full_plan = plan
                subscription.queued_tokens_amount = tokens
            subscription.save()
        else:
            # Create new subscription or replace inactive one
            subscription.token_plan = payment.token_plan
            subscription.full_plan = payment.full_plan
            subscription.tokens_remaining = tokens
            subscription.start_date = timezone.now()
            
            # Set end date for full plans
            if duration_days:
                subscription.end_date = timezone.now() + timedelta(days=duration_days)
            else:
                subscription.end_date = None
            
            subscription.is_active = True
            subscription.status = 'active'
            subscription.cancel_at_period_end = False
            subscription.canceled_at = None
            subscription.save()

        # Link payment to subscription
        payment.subscription = subscription
        payment.save()
