from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from accounts.serializers import DeleteAccountSerializer
from accounts.functions import expire


class DeleteAccountAPIView(APIView):
    serializer_class = DeleteAccountSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Delete user account permanently
        Requires password confirmation and typing 'DELETE' to confirm
        """
        serializer = self.serializer_class(
            data=request.data, 
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = request.user
            
            # Get current access token to expire it
            access_from_cookie = request.COOKIES.get(
                "HTTP_ACCESS"
            ) or request.COOKIES.get("HTTP_AUTHORIZATION")
            access_from_header = request.META.get(
                "HTTP_ACCESS"
            ) or request.META.get("HTTP_AUTHORIZATION")
            access_token = access_from_cookie or access_from_header
            
            # Expire the current JWT tokens
            if access_token:
                expire(access_token)
            
            # Clean up profile picture file if it's not the default
            if (user.profile_picture and 
                user.profile_picture.name != "user_img/default.png"):
                try:
                    # Use storage backend's delete method (works with S3 and local storage)
                    if user.profile_picture.storage.exists(user.profile_picture.name):
                        user.profile_picture.storage.delete(user.profile_picture.name)
                except Exception:
                    # Continue with deletion even if file removal fails
                    pass
            
            # Store user info for response before deletion
            user_email = user.email
            
            # Delete the user account (cascading will handle related objects)
            user.delete()
            
            # Create response and clear authentication cookies
            response = Response(
                {
                    "message": "Account deleted successfully",
                    "deleted_user": user_email
                }, 
                status=status.HTTP_200_OK
            )
            
            # Clear authentication cookies
            response.delete_cookie("HTTP_ACCESS")
            response.set_cookie(
                "HTTP_ACCESS",
                "",
                path="/",
                secure=False,
                httponly=True,
                samesite="None",
                max_age=0,
            )
            
            return response
        
        return Response(
            serializer.errors, 
            status=status.HTTP_400_BAD_REQUEST
        ) 