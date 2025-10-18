from settings.serializers import TelegramChannelSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from settings.models import Settings,TelegramChannel
import requests
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import os
from urllib.parse import urlparse
from core.utils import get_active_proxy


class TeleBotAPIView(APIView):
    serializer_class = TelegramChannelSerializer
    permission_classes = [IsAuthenticated]
    def get(self, *args, **kwargs):
        try:
            bot = TelegramChannel.objects.filter(user=self.request.user).last()
            if not bot:
                return Response("No bot found for this user", status=status.HTTP_404_NOT_FOUND)
            serializer = self.serializer_class(bot, context={'request': self.request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except:
            return Response("Bot not found or something went wrong, try again", status=status.HTTP_400_BAD_REQUEST)



class ConnectTeleAPIView(APIView):
    serializer_class = TelegramChannelSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        bot_token = request.data.get("bot_token")
        if not bot_token:
            return Response({"error": "bot_token is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Get bot information from Telegram API
        try:
            bot_info = self._get_bot_info(bot_token)
            bot_username = bot_info.get("username")
            if not bot_username:
                return Response(
                    {"error": "Could not retrieve bot username from Telegram API"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
            # Get bot profile picture
            profile_picture_file = self._get_bot_profile_picture(bot_token, bot_username)
        except requests.exceptions.RequestException as e:
            return Response(
                {"error": f"Failed to connect to Telegram API: {str(e)}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"Invalid bot token or API error: {str(e)}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Prepare data for serializer
        data = request.data.copy()
        data["user"] = request.user.id
        data["bot_username"] = bot_username

        serializer = self.serializer_class(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_406_NOT_ACCEPTABLE)

        channel = serializer.save()
        
        # Save profile picture if obtained
        if profile_picture_file:
            channel.profile_picture.save(
                f"{bot_username}_profile.jpg",
                profile_picture_file,
                save=True
            )
        
        webhook_url = self._build_webhook_url(bot_token, bot_username)

        try:
            # ✅ استفاده از پروکسی برای ست کردن webhook در Telegram
            response = requests.post(webhook_url, proxies=get_active_proxy())
            if response.status_code == 200:
                channel.is_connect = True
                channel.save()
            else:
                return Response(
                    {"error": f"Telegram API responded with status {response.status_code}: {response.text}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except requests.exceptions.RequestException as e:
            # Optional: log the error using Django's logging
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(self.serializer_class(channel, context={'request': request}).data, status=status.HTTP_201_CREATED)

    def _get_bot_info(self, bot_token):
        """
        Gets bot information from Telegram API using the getMe method.
        """
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        # ✅ استفاده از پروکسی برای دریافت اطلاعات bot از Telegram
        response = requests.get(url, proxies=get_active_proxy())
        
        if response.status_code != 200:
            raise Exception(f"Telegram API error: {response.status_code} - {response.text}")
        
        data = response.json()
        if not data.get("ok"):
            raise Exception(f"Telegram API returned error: {data.get('description', 'Unknown error')}")
        
        return data.get("result")

    def _get_bot_profile_picture(self, bot_token, bot_username):
        """
        Downloads and returns the bot's profile picture from Telegram API.
        Returns ContentFile if successful, None if no picture or error.
        """
        try:
            # Get bot's user profile photos
            url = f"https://api.telegram.org/bot{bot_token}/getUserProfilePhotos"
            params = {"user_id": self._get_bot_user_id(bot_token), "limit": 1}
            # ✅ استفاده از پروکسی برای دریافت عکس پروفایل bot
            response = requests.get(url, params=params, proxies=get_active_proxy())
            
            if response.status_code != 200:
                return None
                
            data = response.json()
            if not data.get("ok") or not data.get("result", {}).get("photos"):
                return None
            
            # Get the first photo's file_id (highest resolution)
            photos = data["result"]["photos"]
            if not photos or not photos[0]:
                return None
                
            photo_sizes = photos[0]  # First photo
            if not photo_sizes:
                return None
                
            # Get the largest size photo
            largest_photo = max(photo_sizes, key=lambda x: x.get("file_size", 0))
            file_id = largest_photo.get("file_id")
            
            if not file_id:
                return None
            
            # Get file path
            file_url = f"https://api.telegram.org/bot{bot_token}/getFile"
            file_params = {"file_id": file_id}
            # ✅ استفاده از پروکسی برای دریافت مسیر فایل
            file_response = requests.get(file_url, params=file_params, proxies=get_active_proxy())
            
            if file_response.status_code != 200:
                return None
                
            file_data = file_response.json()
            if not file_data.get("ok"):
                return None
                
            file_path = file_data["result"].get("file_path")
            if not file_path:
                return None
            
            # Download the actual file
            download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
            # ✅ استفاده از پروکسی برای دانلود فایل عکس
            download_response = requests.get(download_url, proxies=get_active_proxy())
            
            if download_response.status_code == 200:
                return ContentFile(download_response.content, name=f"{bot_username}_profile.jpg")
                
        except Exception as e:
            # Log error but don't fail the bot connection
            print(f"Error downloading bot profile picture: {str(e)}")
            
        return None
    
    def _get_bot_user_id(self, bot_token):
        """
        Gets the bot's user ID from Telegram API.
        """
        try:
            bot_info = self._get_bot_info(bot_token)
            return bot_info.get("id")
        except Exception:
            return None

    def _build_webhook_url(self, bot_token, bot_username):
        """
        Builds the full Telegram API webhook URL for setting the bot's webhook.
        """
        base_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
        webhook_target = f"https://api.pilito.com/api/v1/message/webhook/{bot_username}/"
        return f"{base_url}?url={webhook_target}"




class DisConnectTeleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, *args, **kwargs):
        bot_name = self.kwargs["bot_name"]
        if not bot_name:
            return Response({"detail": "Bot name is required."},status=status.HTTP_400_BAD_REQUEST)

        try:
            bot = TelegramChannel.objects.get(bot_username=bot_name)
        except TelegramChannel.DoesNotExist:
            return Response({"detail": "Bot not found."}, status=status.HTTP_404_NOT_FOUND)

        if bot.user != self.request.user:
            return Response({"detail": "You do not have permission to remove this bot."},status=status.HTTP_403_FORBIDDEN)

        bot.delete()
        return Response({"detail": "Bot removed successfully."},status=status.HTTP_200_OK)