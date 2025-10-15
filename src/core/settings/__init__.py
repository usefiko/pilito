from os import environ
from dotenv import load_dotenv

load_dotenv()
stage = environ.get("STAGE")

if not stage:
    raise ValueError("STAGE is not set")
if stage == "PRODUCTION":
    from core.settings.production import *
elif stage == "DEV":
    from core.settings.development import *
else:
    raise ValueError("STAGE is not correct!")
