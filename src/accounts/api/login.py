from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from accounts.serializers import LoginSerializer
from core.settings import ACCESS_TTL

class LoginAPIView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            response = Response(serializer.validated_data, status=status.HTTP_200_OK)
            response.set_cookie(
                key="HTTP_ACCESS",  # or "jwt" depending on your code
                value=f"Bearer {serializer.validated_data['access_token']}",
                httponly=True,
                max_age=ACCESS_TTL * 24 * 3600,
                secure=False,  # set to False for local development
                samesite='Lax')
            return response
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)