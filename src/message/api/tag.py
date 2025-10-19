from rest_framework.views import APIView
from rest_framework.response import Response
from message.serializers import TagSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from message.models import Tag


class TagsAPIView(APIView):
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        try:
            # فقط تگ‌هایی که این user ساخته
            tags = Tag.objects.filter(
                created_by=request.user
            ).exclude(name__in=["Telegram", "Whatsapp", "Instagram"]).order_by('-created_at')
            
            serializer = self.serializer_class(tags, many=True)
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
                # وقتی تگ جدید می‌سازیم، created_by را set می‌کنیم
                if isinstance(serializer.validated_data, list):
                    # برای لیست تگ‌ها
                    tags = [Tag(created_by=request.user, **item) for item in serializer.validated_data]
                    Tag.objects.bulk_create(tags)
                    return Response(TagSerializer(tags, many=True).data, status=status.HTTP_201_CREATED)
                else:
                    # برای تگ تکی
                    serializer.save(created_by=request.user)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": f"Error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

