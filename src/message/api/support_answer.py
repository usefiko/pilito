from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from message.models import Message,Conversation,Customer
from message.serializers import MessageSerializer,MessageSupportAnswerSerializer
from rest_framework.permissions import IsAuthenticated


class SupportAnswerAPIView(APIView):
    serializer_class = MessageSupportAnswerSerializer
    permission_classes = [IsAuthenticated]
    def post(self, *args, **kwargs):
        try:
            data = self.request.data
            data["type"] = "support"
            conv = Conversation.objects.get(id=self.kwargs["id"])
            data["conversation"] = conv.id
            data["customer"] = conv.customer.id
            serializer = self.serializer_class(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_406_NOT_ACCEPTABLE)
        except Exception as e:
            return Response(f"error: {str(e)}", status=status.HTTP_400_BAD_REQUEST)