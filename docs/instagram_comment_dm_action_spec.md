
# 📦 Spec: Instagram Comment → DM + Public Reply Action

این فایل برای پیاده‌سازی **اکشن جدید ورک‌فلو** در فیکو است که:

- وقتی روی **کامنت اینستاگرام** تریگر می‌خورد،
- هم‌زمان:
  - به کاربر **دایرکت** می‌فرستد
  - و زیر همان کامنت یک **ریپلای عمومی** ثبت می‌کند.

تریگر را دست نمی‌زنیم؛ فقط اکشن جدید اضافه می‌کنیم.  
فرض: تریگر از قبل با event_type مناسب (مثلاً `INSTAGRAM_COMMENT_CREATED`) تنظیم شده و `TriggerEventLog` دیتا را دارد.

---

## 1. پیش‌نیازهای اینستاگرام (Graph API)

این اکشن فقط برای **Instagram Business / Creator** که از طریق Graph متصل شده‌اند فعال است.

Permission‌های لازم:

- برای **کامنت‌ها**:
  - `instagram_business_manage_comments`
- برای **دایرکت** (قبلاً در فیکو استفاده شده):
  - `instagram_manage_messages`
  - به‌همراه `pages_messaging` روی پیج فیس‌بوک متصل (قبلاً برای DM دارید)

Endpoints اصلی:

- **ارسال دایرکت** (قبلاً در سیستم هست، از همون سرویس استفاده می‌کنیم)
- **ریپلای به کامنت**:
  ```http
  POST https://graph.facebook.com/v21.0/{comment-id}/replies
  Content-Type: application/json
  Body:
  {
    "message": "متن ریپلای",
    "access_token": "<PAGE_OR_IG_ACCESS_TOKEN>"
  }
  ```

---

## 2. اکشن جدید در سیستم ورک‌فلو

### 2.1. نام اکشن

در مدل اکشن‌ها (هرجا که action_type تعریف می‌کنید) یک نوع جدید اضافه کنید:

```python
# مثال: در workflow/models.py یا هر جایی که ACTION_TYPE_CHOICES دارید
ACTION_TYPE_CHOICES = [
    # ...
    ('instagram_comment_dm_reply', 'Instagram Comment → DM + Reply'),
]
```

---

## 3. ساختار config برای این اکشن

Config این اکشن در DB (مثلاً `WorkflowAction.config`) به‌صورت JSON ذخیره می‌شود.

### 3.1. اسکیما

```json
{
  "dm_mode": "STATIC" | "PRODUCT",
  "dm_text_template": "string (optional, required if dm_mode=STATIC)",
  "product_id": "string (optional, required if dm_mode=PRODUCT)",
  "public_reply_enabled": true,
  "public_reply_template": "string"
}
```

### 3.2. توضیح فیلدها

- `dm_mode`  
  - `"STATIC"` → دایرکت ثابت (بدون AI / بدون محصول)  
  - `"PRODUCT"` → دایرکت AI بر اساس محصول انتخاب‌شده

- `dm_text_template` (فقط وقتی `dm_mode = STATIC`)  
  - رشته‌ی قالب دایرکت، با Placeholderهای زیر:
    - `{username}` → نام کاربر اینستاگرام
    - `{comment_text}` → متن کامنت
    - `{post_url}` → لینک پست (اگر در event_data موجود باشد)

- `product_id` (فقط وقتی `dm_mode = PRODUCT`)  
  - شناسه محصول در مدل Product/Knowledge (مثلاً `TenantProduct.id` یا هر مدلی که دارید)

- `public_reply_enabled`:  
  - `true` → زیر کامنت هم ریپلای ارسال شود  
  - `false` → فقط دایرکت

- `public_reply_template`:  
  - متن ریپلای عمومی زیر کامنت، با Placeholderهای:
    - `{username}`
    - `{product_name}` (فقط وقتی dm_mode=PRODUCT و محصول یافت شد)
  - **پیشنهاد:** متن پیش‌فرض بدون قیمت باشد، مثلاً:
    > "قیمت و جزئیات رو دایرکت برات فرستادم {username} ✨"

---

## 4. داده‌ی ورودی مورد انتظار از Event Log

اکشن فرض می‌کند `WorkflowExecution` از یک `TriggerEventLog` آمده که `context_data["event"]` تقریباً این‌شکل باشد:

```json
{
  "type": "INSTAGRAM_COMMENT_CREATED",
  "conversation_id": null,
  "user_id": "<internal_user_id>",
  "data": {
    "comment_id": "<instagram_comment_id>",
    "comment_text": "سلام، قیمتش چنده؟",
    "post_id": "<instagram_media_id>",
    "post_url": "https://www.instagram.com/p/xyz/",
    "ig_username": "customer_username",
    "ig_user_id": "<instagram_user_id>",
    "channel_id": "<InstagramChannel.id>"
  }
}
```

حداقل فیلدهای لازم در `event["data"]`:

- `comment_id`
- `comment_text`
- `ig_username`
- `ig_user_id`
- `channel_id`  
`post_url` اختیاری است (برای template دایرکت استفاده می‌شود).

---

## 5. تغییر در WorkflowExecutionService برای این اکشن

در سرویس اجرای اکشن‌ها (مثلاً `WorkflowExecutionService._execute_workflow_action`) یک case جدید اضافه کنید:

```python
if workflow_action.action_type == 'instagram_comment_dm_reply':
    from workflow.services.instagram_comment_action import handle_instagram_comment_dm_reply

    event = (workflow_execution.context_data or {}).get('event', {})
    event_data = event.get('data', {}) if isinstance(event, dict) else {}

    handle_instagram_comment_dm_reply(
        workflow_execution=workflow_execution,
        workflow_action=workflow_action,
        event_data=event_data,
        user=workflow_execution.user  # یا owner واقعی workflow
    )
```

نام فیلدها را با مدل واقعی خودتان هماهنگ کنید.

---

## 6. سرویس جدید: `instagram_comment_action.py`

فایل جدید: `workflow/services/instagram_comment_action.py`

```python
import logging
from typing import Dict, Any
from django.template import Template, Context

from message.services.instagram_service import InstagramService
from knowledge.models import Product  # یا مدل واقعی محصول شما
from AI_model.services.gemini_service import GeminiService

logger = logging.getLogger(__name__)


def render_template(template_str: str, context: Dict[str, Any]) -> str:
    """
    Simple template rendering using Django Template engine.
    """
    try:
        t = Template(template_str)
        c = Context(context)
        return t.render(c).strip()
    except Exception as e:
        logger.warning(f"Failed to render template: {e}")
        return template_str


def handle_instagram_comment_dm_reply(workflow_execution, workflow_action, event_data: Dict[str, Any], user):
    """
    Main handler for 'instagram_comment_dm_reply' action.
    - Sends DM to comment author (static or product-based)
    - Optionally posts public reply under the comment
    """
    config = workflow_action.config or {}
    dm_mode = config.get('dm_mode')
    dm_text_template = config.get('dm_text_template', '')
    product_id = config.get('product_id')
    public_reply_enabled = config.get('public_reply_enabled', False)
    public_reply_template = config.get('public_reply_template', '')

    # Basic validation
    if dm_mode not in ['STATIC', 'PRODUCT']:
        logger.error(f"[InstagramCommentAction] Invalid dm_mode: {dm_mode}")
        return

    if dm_mode == 'STATIC' and not dm_text_template:
        logger.error("[InstagramCommentAction] dm_text_template is required for STATIC mode")
        return

    if dm_mode == 'PRODUCT' and not product_id:
        logger.error("[InstagramCommentAction] product_id is required for PRODUCT mode")
        return

    # Extract event data
    comment_id = event_data.get('comment_id')
    comment_text = event_data.get('comment_text') or ''
    post_url = event_data.get('post_url') or ''
    ig_username = event_data.get('ig_username') or ''
    ig_user_id = event_data.get('ig_user_id')
    channel_id = event_data.get('channel_id')

    if not (comment_id and ig_user_id and channel_id):
        logger.error(f"[InstagramCommentAction] Missing required fields in event_data: {event_data}")
        return

    # Get Instagram service for this channel
    instagram_service = InstagramService.get_service_for_channel_id(channel_id)
    if not instagram_service:
        logger.error(f"[InstagramCommentAction] Could not get InstagramService for channel_id={channel_id}")
        return

    # Base context for templates
    base_ctx = {
        'username': ig_username,
        'comment_text': comment_text,
        'post_url': post_url,
    }

    # 1) Send DM
    dm_result = None
    product = None

    if dm_mode == 'STATIC':
        dm_text = render_template(dm_text_template, base_ctx)
        dm_result = instagram_service.send_dm_by_instagram_id(
            ig_user_id=ig_user_id,
            text=dm_text
        )
        logger.info(f"[InstagramCommentAction] STATIC DM sent to {ig_username} result={dm_result}")

    elif dm_mode == 'PRODUCT':
        # Load product
        try:
            product = Product.objects.get(id=product_id, user=user)
        except Product.DoesNotExist:
            logger.error(f"[InstagramCommentAction] Product {product_id} not found for user {user.id}")
            return

        # Build AI prompt context
        ai_service = GeminiService.get_for_user(user)
        ai_response = ai_service.generate_product_dm_for_instagram_comment(
            comment_text=comment_text,
            product=product,
            extra_context={
                'username': ig_username,
                'post_url': post_url,
            }
        )

        if not ai_response.get('success'):
            logger.error(f"[InstagramCommentAction] AI failed for product DM: {ai_response}")
            return

        dm_text = ai_response['response']
        dm_result = instagram_service.send_dm_by_instagram_id(
            ig_user_id=ig_user_id,
            text=dm_text
        )
        logger.info(f"[InstagramCommentAction] PRODUCT DM sent to {ig_username} result={dm_result}")

    # 2) Public reply under the comment (optional)
    if public_reply_enabled and public_reply_template:
        reply_ctx = dict(base_ctx)
        if product:
            reply_ctx['product_name'] = getattr(product, 'name', '')

        reply_text = render_template(public_reply_template, reply_ctx)
        if reply_text:
            reply_result = instagram_service.reply_to_comment(
                comment_id=comment_id,
                text=reply_text
            )
            logger.info(f"[InstagramCommentAction] Public reply under comment {comment_id} result={reply_result}")
```

> نام متدها (`get_service_for_channel_id`, `send_dm_by_instagram_id`, `reply_to_comment`, `generate_product_dm_for_instagram_comment`) باید با ساختار واقعی پروژه هماهنگ شوند. این‌ها اینترفیس پیشنهادی هستند.

---

## 7. تغییرات در InstagramService

در `message/services/instagram_service.py` متدهای زیر را اضافه/آداپت کنید:

```python
class InstagramService:
    # ...

    @classmethod
    def get_service_for_channel_id(cls, channel_id: str):
        """
        Create InstagramService instance for given InstagramChannel.id
        """
        from message.models import InstagramChannel
        try:
            channel = InstagramChannel.objects.get(id=channel_id)
        except InstagramChannel.DoesNotExist:
            return None
        return cls(access_token=channel.access_token, instagram_user_id=channel.instagram_user_id)

    def send_dm_by_instagram_id(self, ig_user_id: str, text: str) -> Dict[str, Any]:
        """
        Send a DM to raw instagram user id using Graph API.
        Implement by adapting existing DM send logic.
        """
        # TODO: implement using /{ig_user_id}/messages or existing method
        raise NotImplementedError

    def reply_to_comment(self, comment_id: str, text: str) -> Dict[str, Any]:
        """
        Reply to an Instagram comment using Graph API.
        Requires instagram_business_manage_comments permission.
        """
        url = f"https://graph.facebook.com/v21.0/{comment_id}/replies"
        payload = {"message": text}
        params = {"access_token": self.access_token}
        headers = {"Content-Type": "application/json"}
        # TODO: implement HTTP POST using requests or existing HTTP client
        raise NotImplementedError
```

Cursor باید این TODOها را با توجه به کد فعلی شما پر کند.

---

## 8. رفتار UI برای این اکشن (Workflow Builder)

وقتی کاربر در پنل مارکتینگ این اکشن را انتخاب می‌کند (`instagram_comment_dm_reply`):

### فیلدها:

- **DM Mode** (رادیو):
  - `( ) ارسال دایرکت ثابت`
  - `( ) ارسال دایرکت با محصول انتخابی`

- اگر *ارسال دایرکت ثابت*:
  - Textarea: **متن دایرکت**  
    Placeholder ها: `{username}`, `{comment_text}`, `{post_url}`

- اگر *ارسال دایرکت با محصول انتخابی*:
  - Dropdown: **انتخاب محصول** (از Productهایی که در نالج ثبت شده)
  - توضیح:  
    > «هوش مصنوعی بر اساس این محصول، قیمت و توضیحات را در دایرکت می‌فرستد. اگر قیمت ثبت نشده باشد، صادقانه اعلام می‌کند.»

- Switch: `[x] زیر کامنت هم ریپلای ثبت شود`
  - اگر روشن بود:
    - Textarea: **متن ریپلای عمومی زیر کامنت**  
      Placeholder ها: `{username}`, `{product_name}`  
      پیش‌فرض پیشنهادی:
      > "قیمت و جزئیات رو دایرکت برات فرستادم {username} ✨"

### ولیدیشن UI:

- اگر `dm_mode = STATIC` و `dm_text_template` خالی → اجازه‌ی Save نده
- اگر `dm_mode = PRODUCT` و `product_id` انتخاب نشده → اجازه‌ی Save نده
- اگر `public_reply_enabled = true` و `public_reply_template` خالی → هشدار/خطا بده

---

## 9. سناریوهای پشتیبانی‌شده

1. **پست تک‌محصولی با قیمت در نالج**  
   - Trigger: کامنت حاوی «قیمت / price / چند»  
   - Action:  
     - `dm_mode = PRODUCT` + انتخاب محصول  
     - `public_reply_enabled = true`  
   - نتیجه:
     - DM: AI قیمت + توضیح کامل  
     - Reply: «قیمت و جزئیات رو دایرکت برات فرستادم {username} ✨»

2. **کمپین بدون قیمت خودکار (فقط هدایت به DM)**  
   - `dm_mode = STATIC`  
   - DM: متن ثابت  
   - Reply: اعلام «دریافت دایرکت»

---

این Spec برای Cursor کاملاً کافی است تا:

- نوع اکشن جدید `instagram_comment_dm_reply` را اضافه کند،
- سرویس آن را در `workflow/services/instagram_comment_action.py` پیاده‌سازی کند،
- و متدهای لازم را در `InstagramService` اضافه/آداپت کند.
