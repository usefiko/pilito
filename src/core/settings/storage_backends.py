from storages.backends.s3boto3 import S3Boto3Storage

class StaticStorage(S3Boto3Storage):
    location = 'static'
    default_acl = 'public-read'
    querystring_auth = False
    # Allow overwriting to avoid 404 errors during collectstatic
    file_overwrite = True
    # Reduce S3 API calls
    gzip = True
    gzip_content_types = [
        'text/css',
        'text/javascript',
        'application/javascript',
        'application/x-javascript',
        'text/xml',
        'application/xml',
        'application/xml+rss',
        'text/plain',
        'text/html',
    ]
    
    def get_modified_time(self, name):
        """
        Override to handle 404 errors gracefully during collectstatic.
        If file doesn't exist in S3, return None to trigger upload.
        """
        try:
            return super().get_modified_time(name)
        except Exception:
            # File doesn't exist, return None so Django will upload it
            return None

class MediaStorage(S3Boto3Storage):
    location = 'media'
    default_acl = 'public-read'
    file_overwrite = False
    querystring_auth = False
    custom_domain = False

# Alternative MediaStorage using pre-signed URLs (use this if ACL issues persist)
class MediaStoragePresigned(S3Boto3Storage):
    location = 'media'
    file_overwrite = False
    querystring_auth = True  # Use pre-signed URLs
    querystring_expire = 3600  # URLs expire in 1 hour
    default_acl = None  # Don't set ACL