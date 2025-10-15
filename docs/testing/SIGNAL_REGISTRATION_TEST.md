# 🧪 Signal Registration Test

## چک کنیم signal ها register شدن یا نه:

```bash
# روی سرور:
docker compose exec web python manage.py shell
```

```python
from django.db.models.signals import post_save
from message.models import Message

# چک کن ببین signal های Message چیه:
receivers = post_save._live_receivers(Message)
print(f"📊 Total registered signals for Message: {len(receivers)}")

for receiver in receivers:
    print(f"  - {receiver.__name__ if hasattr(receiver, '__name__') else receiver}")

# چک کن ببین signal خاص ما هست یا نه:
has_contact_extraction = any('ai_contact_extraction' in str(r) or 'handle_ai_message_processing' in str(r) for r in receivers)
print(f"\n✅ Contact Extraction Signal: {'REGISTERED' if has_contact_extraction else '❌ NOT FOUND'}")

exit()
```

اگه signal نبود، یعنی مشکل از `apps.py` هست.