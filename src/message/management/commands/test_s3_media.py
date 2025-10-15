from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import tempfile
import requests
from PIL import Image
import io


class Command(BaseCommand):
    help = 'Test S3 media storage configuration'

    def handle(self, *args, **options):
        self.stdout.write("Testing S3 Media Storage...")
        
        try:
            # Create a test image
            img = Image.new('RGB', (100, 100), color='red')
            img_io = io.BytesIO()
            img.save(img_io, 'JPEG', quality=70)
            img_io.seek(0)
            
            # Upload test file
            test_file = ContentFile(img_io.getvalue(), name='test_image.jpg')
            file_path = default_storage.save('test_uploads/test_image.jpg', test_file)
            
            self.stdout.write(f"✅ File uploaded successfully: {file_path}")
            
            # Get the URL
            file_url = default_storage.url(file_path)
            self.stdout.write(f"📁 File URL: {file_url}")
            
            # Test if the file is accessible
            try:
                response = requests.get(file_url)
                if response.status_code == 200:
                    self.stdout.write("✅ File is publicly accessible!")
                else:
                    self.stdout.write(f"❌ File not accessible. Status code: {response.status_code}")
                    self.stdout.write(f"Response: {response.text}")
            except Exception as e:
                self.stdout.write(f"❌ Error accessing file: {str(e)}")
            
            # Clean up
            try:
                default_storage.delete(file_path)
                self.stdout.write("🗑️ Test file cleaned up")
            except Exception as e:
                self.stdout.write(f"⚠️ Could not delete test file: {str(e)}")
                
        except Exception as e:
            self.stdout.write(f"❌ Error during test: {str(e)}")
            
        self.stdout.write("\nS3 Media Storage test completed.") 