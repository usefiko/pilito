from rest_framework.views import APIView
from rest_framework.response import Response
from message.serializers import TagSerializer
from rest_framework.permissions import AllowAny
from rest_framework import status
from message.models import Tag


class TagsAPIView(APIView):
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    def get(self, *args, **kwargs):
        try:
            tag = Tag.objects.exclude(name__in=["Telegram", "Whatsapp", "Instagram"])
            serializer = self.serializer_class(tag, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(f"Error: {str(e)}", status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, *args, **kwargs):
        try:
            data = request.data

            # Support multiple input formats: list of objects, list of names, or single object
            if isinstance(data, dict) and "names" in data and isinstance(data["names"], list):
                prepared = [{"name": str(name).strip()} for name in data["names"] if str(name).strip()]
                if not prepared:
                    return Response({"detail": "No valid tag names provided."}, status=status.HTTP_400_BAD_REQUEST)
                serializer = self.serializer_class(data=prepared, many=True)
            elif isinstance(data, list):
                serializer = self.serializer_class(data=data, many=True)
            else:
                serializer = self.serializer_class(data=data)

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": f"Error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

