from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.serializers import UserSerializer,UserUpdateSerializer,UserProfilePictureSerializer,UserOverviewSerializer
from rest_framework.permissions import IsAuthenticated
from django.conf import settings

class Profile(APIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get(self, *args, **kwargs):
        serializer = self.serializer_class(self.request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, *args, **kwargs):
        serializer = UserUpdateSerializer(self.request.user, data=self.request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_406_NOT_ACCEPTABLE)


class ProfilePicture(APIView):
    serializer_class = UserProfilePictureSerializer
    permission_classes = [IsAuthenticated]
    def post(self, *args, **kwargs):
        serializer = self.serializer_class(self.request.user, data=self.request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_406_NOT_ACCEPTABLE)



class ProfilePictureRemove(APIView):
    permission_classes = [IsAuthenticated]
    def delete(self, *args, **kwargs):
        user = self.request.user
        
        # If user has a custom profile picture (not the default), delete the file
        if user.profile_picture and user.profile_picture.name != "user_img/default.png":
            try:
                # Use the storage backend's delete method instead of local file operations
                # This works with both local storage and cloud storage (S3, etc.)
                if user.profile_picture.storage.exists(user.profile_picture.name):
                    user.profile_picture.storage.delete(user.profile_picture.name)
            except Exception as e:
                # Log the error but continue with database update
                # This handles any storage backend errors gracefully
                print(f"Error deleting profile picture: {e}")
                pass
        
        # Reset to default profile picture
        user.profile_picture = "user_img/default.png"
        user.save()
        
        # Return the updated user data
        serializer = UserSerializer(user)
        return Response({
            "message": "Profile picture removed successfully",
            "user": serializer.data
        }, status=status.HTTP_200_OK)


class UserOverview(APIView):
    serializer_class = UserOverviewSerializer
    permission_classes = [IsAuthenticated]

    def get(self, *args, **kwargs):
        serializer = self.serializer_class(self.request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

