from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from billing.serializers import PurchasesSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from billing.models import Purchases
import json
import requests
from django.conf import settings
from core.responses import bad_request, SuccessResponse, UnsuccessfulResponse
from django.http import HttpResponse,JsonResponse
from django.db import transaction
from django.shortcuts import redirect
from accounts.models import Plan


class Payment(APIView):
    serializer_class = PurchasesSerializer
    permission_classes = [IsAuthenticated]

    def post(self, *args, **kwargs):
        authority = self.request.query_params.get("Authority")
        status = self.request.query_params.get("Status")
        data = self.request.data
        data["user"] = self.request.user.id
        data["description"] = self.request.data["name"]

        serializer = self.serializer_class(data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            purchase = Purchases.objects.get(id=serializer.data['id'])

            data = {
                "MerchantID": settings.ZARRINPAL_MERCHANT_ID,
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
            return redirect('https://fiko.net/panel/callback?success=notok')
            #return HttpResponse("payment faild...", content_type='text/plain')

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

                plan = Plan.objects.get(user=purchase.user)
                plan.days += purchase.price # todo - update plan filds
                plan.save()

                return redirect(f'https://fiko.net/panel/callback?success=ok&payment_id={response["RefID"]}')
                #return HttpResponse("payment done, RefID={}".format(response['RefID']), content_type='text/plain')
            else:
                return SuccessResponse(data={'status': False, 'details': 'purchase already paid' })
        return SuccessResponse(data=response.content)