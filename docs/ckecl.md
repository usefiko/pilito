جواب کوتاه:
مدل‌هات و وبهوک اینستا به‌طور کلی با اون معماری‌ای که با هم چیدیم سازگارند 👍 ولی چندتا نکته مهم و چندتا باگ/ناکامل‌بودن ریز دارن که قبل از سپردن به Cursor بهتره فیکس‌شون کنی.

می‌رم بخش‌به‌بخش جلو 👇

⸻

1️⃣ مدل‌های Workflow / Node / Trigger

✅ چیزهایی که درسته
	•	Trigger.TRIGGER_TYPE_CHOICES

('INSTAGRAM_COMMENT', 'Instagram Comment'),

اوکیه؛ هم تریگر کلاسیک داری، هم در WhenNode.WHEN_TYPE_CHOICES:

('instagram_comment', 'Instagram Comment'),

یعنی هم ورک‌فلو قدیمی، هم نود‌بیس آماده هست.

	•	Action.ACTION_TYPE_CHOICES و ActionNode.ACTION_TYPE_CHOICES
هر دو جا instagram_comment_dm_reply رو اضافه کردی؛ این عالیه چون:
	•	در ورک‌فلو کلاسیک از Action استفاده می‌کنی
	•	در نود‌بیس از ActionNode و فیلدهای instagram_dm_* استفاده می‌کنی
	•	TriggerEventLog
فیلدها:

event_type = models.CharField(...)
event_data = models.JSONField(...)
user_id = models.CharField(...)
conversation_id = models.CharField(...)

و توی وبهوک:

TriggerEventLog.objects.create(
    event_type='INSTAGRAM_COMMENT',
    user_id=str(channel.user.id),
    conversation_id=None,
    event_data=event_data
)

این دقیقاً همون چیزیه که برای ایزوله‌کردن هر یوزر لازم داریم. ✅

⚠️ نکته مهم 1: config اکشن از کجاست؟

الان تو مدل‌ها اینطوریه:
	•	Action → فیلد configuration داره ✅
	•	WorkflowAction → هیچ فیلد config نداره ❌

و تو WorkflowExecutionService._execute_action هم اینه:

config = substitute_template_placeholders(action.configuration, context)

پس برای اکشن instagram_comment_dm_reply در ورک‌فلو کلاسیک باید تنظیمات رو توی همون Action.configuration نگه داریم، نه WorkflowAction.

من قبلاً برات سرویسی نوشته بودم که workflow_action.config می‌خوند؛
اینو باید به این شکل اصلاح کنیم:
	•	تو instagram_comment_action.py (یا هر سرویسی که می‌سازی) به جای workflow_action.config از action.configuration استفاده کنی.
	•	یا اگر می‌خوای per-workflow config داشته باشی، لازمه تو مدل WorkflowAction یک فیلد config = JSONField(default=dict, ...) اضافه کنی و بعد کد WorkflowExecutionService رو هم آپدیت کنی.
(برای MVP پیشنهاد می‌کنم فعلاً روی همون Action.configuration بمونی که ساده‌تره.)

⚠️ نکته مهم 2: Node-based Export / Import

توی مدل Workflow.import_from_dict و export_to_dict، برای WhenNode و ActionNode فقط فیلدهای قدیمی رو هندل می‌کنی:
	•	برای WhenNode تو export:

'when_type', 'keywords', 'tags', 'channels',
'schedule_frequency', 'schedule_start_date', 'schedule_time'

ولی فیلدهای جدیدت:

instagram_post_url
instagram_media_type
comment_keywords

اصلاً export / import نمی‌شن → وقتی یک ورک‌فلو رو export/import کنی، این تنظیم‌ها گم می‌شن.

	•	برای ActionNode هم همین مشکل رو داری؛ فیلدهای:

instagram_dm_mode
instagram_dm_text_template
instagram_product_id
instagram_public_reply_enabled
instagram_public_reply_text

نه در export_to_dict ذخیره می‌شن، نه در import_from_dict دوباره ساخته می‌شن.

🛠 پیشنهاد:
بعداً که وقت داشتی، تو دو جای زیر این فیلدها رو اضافه کن:
	•	در export_to_dict → بخش whennode و actionnode
	•	در import_from_dict → جایی که WhenNode.objects.create و ActionNode.objects.create را صدا می‌زنی

برای MVP اگر فعلاً export/import استفاده نمی‌کنی، می‌تونی این رو بذاری مرحله بعد، ولی حواست باشه.

⸻

2️⃣ وبهوک Instagram (InstaWebhook)

✅ چیزهای خوب
	•	verify توکن ساده و درست:

mode == 'subscribe' and token == VERIFY_TOKEN


	•	در post:
	•	چک می‌کنی object == 'instagram'
	•	برای هر entry → _process_entry
	•	در _process_entry:
	•	اول changes رو چک می‌کنی (کامنت‌ها) ✅
	•	اگر کامنتی پردازش شد، return processed_messages → یعنی با DMها قاطی نمی‌کنی (که منطقیه، معمولاً کامنت و مسیج تو یک entry نمیاد)
	•	اگر changes نبود یا خروجی نداشت، میره سراغ messaging برای دایرکت‌ها

✅ لاجیک کامنت‌ها (_process_comment)
	•	از entry['id'] → page_id
	•	از change['value'] → comment_data
	•	پارس:

comment_id = comment_data.get('id')
comment_text = comment_data.get('text', '')
from_user = comment_data.get('from', {})
media = comment_data.get('media', {})
ig_user_id = from_user.get('id')
ig_username = from_user.get('username', '')
media_id = media.get('id')


	•	پیدا کردن InstagramChannel با:

InstagramChannel.objects.get(instagram_user_id=page_id, is_connect=True)


	•	استفاده از:

instagram_service = InstagramService.get_service_for_channel_id(str(channel.id))
post_url = instagram_service.get_media_permalink(media_id)

(اینو حتماً باید تو InstagramService پیاده کرده باشی، وگرنه اینجا کرش می‌کنه.)

	•	ساخت event_data:

{
    'comment_id': comment_id,
    'comment_text': comment_text,
    'post_id': media_id,
    'post_url': post_url,
    'media_type': media_type,
    'ig_username': ig_username,
    'ig_user_id': ig_user_id,
    'channel_id': str(channel.id),
    'page_id': page_id,
}

این دقیقاً همون چیزیه که برای تریگر و اکشن نیاز داریم. ✅

	•	ساخت TriggerEventLog:

TriggerEventLog.objects.create(
    event_type='INSTAGRAM_COMMENT',
    user_id=str(channel.user.id),
    conversation_id=None,
    event_data=event_data
)


	•	سپس:

from workflow.tasks import process_event
process_event.delay(str(event_log.id))

→ مسیر درسته.

⚠️ نکته مهم 3: TriggerService باید user_id رو درست استفاده کنه

مدل TriggerEventLog اینه:

user_id = models.CharField(...)

یعنی FK به User نداری، فقط یک char ذخیره می‌کنی.

پس در TriggerService (یا هر جایی که owner ورک‌فلو رو پیدا می‌کنی)، برای INSTAGRAM_COMMENT باید:
	•	از event_log.user_id استفاده کنی به عنوان workflow_owner_id
	•	یا از event_log.event_data['channel_id'] → InstagramChannel.user

چیزی که توی کد فعلیت باید چک کنی:

# pseudo
if event_log.event_type == 'INSTAGRAM_COMMENT':
    owner_id = event_log.user_id  # ما قبلاً همون channel.user.id رو اینجا گذاشتیم

و بعد این owner_id رو در context بگذاری (مثلاً workflow_owner_id) تا توی WorkflowExecutionService بتونی آن یوزر رو لود کنی.

⸻

⚠️ نکته مهم 4: متدهای لازم روی InstagramService

از این فایل، تو اینستا سرویس انتظار داری:
	1.	InstagramService.get_service_for_channel_id(channel_id: str)
	2.	InstagramService.get_media_permalink(media_id: str)

اگر هنوز کامل پیاده‌شون نکردی، حتماً:

# message/services/instagram_service.py

@classmethod
def get_service_for_channel_id(cls, channel_id):
    from settings.models import InstagramChannel
    channel = InstagramChannel.objects.get(id=channel_id, is_connect=True)
    return cls(channel.access_token, channel.instagram_user_id)

def get_media_permalink(self, media_id: str) -> Optional[str]:
    """
    Call Graph API:
    GET https://graph.facebook.com/v21.0/{media_id}?fields=permalink&access_token=...
    """
    ...

وگرنه اولین کامنتی که بیاد، این خط:

post_url = instagram_service.get_media_permalink(media_id)

با AttributeError می‌ترکه.

⸻

⚠️ نکته مهم 5: متد تکراری _download_profile_picture

تو همین فایل دو تا تعریف برای _download_profile_picture داری 😅
	•	یکی وسط کلاس
	•	یکی نزدیک پایین کلاس

پایتون دومی رو می‌ذاره روی اولی، پس از نظر runtime مشکلی پیش نمیاد، ولی:
	•	خوانایی کد رو خراب می‌کنه
	•	اگر یکی رو بعداً ادیت کنی و اون یکی یادت بره، فاجعه می‌شه

🛠 حتماً یکی‌ش رو حذف کن و فقط یک نسخه نگه دار.

⸻

⚠️ نکته مهم 6: API ای که برای user info استفاده می‌کنی

این قسمت:

url = f"https://graph.instagram.com/v23.0/{user_id}"
params = {
    'fields': 'id,name,username,profile_pic,is_verified_user,follower_count',
    'access_token': access_token
}

	•	graph.instagram.com در اصل برای Instagram Basic Display API هست، نه Business Messaging.
	•	تو پرمیشن‌هایی که گفتی (instagram_business_* و graph API فیسبوک) معمولاً از graph.facebook.com/v21.0/... استفاده می‌شه.

اگر الان داری جواب درست می‌گیری، اوکی؛ ولی اگر:
	•	همیشه خالی برمی‌گرده
	•	یا ارور Unsupported get request می‌گیری

باید این رو بعداً با داک رسمی متا مچ کنی. برای MVP می‌تونیم همینو نگه داریم و rely کنیم روی فیلدهای پایه تو وبهوک.

⸻

3️⃣ جمع‌بندی عملی برای الان

✅ چیزهایی که برای MVP حتماً انجام بده
	1.	اینستا وبهوک
	•	یکی از دو تا _download_profile_picture رو حذف کن.
	•	مطمئن شو InstagramService.get_service_for_channel_id و get_media_permalink پیاده شدن.
	2.	Trigger / Workflow
	•	در TriggerService برای INSTAGRAM_COMMENT بگو owner همون event_log.user_id هست.
	•	در WorkflowExecutionService._execute_action:
	•	case جدید برای instagram_comment_dm_reply اضافه کن.
	•	چون config روی Action.configuration هست، از همون بخون و به هندر کامنت پاس بده.
	3.	Node-based
	•	برای الان اگر node-based workflow کامنت رو استفاده نمی‌کنی → اوکیه.
	•	اگر می‌خوای از نودها استفاده کنی، بعداً:
	•	فیلدهای instagramی WhenNode و ActionNode رو تو export/import اضافه کن.
	•	تو NodeBasedWorkflowExecutionService هم یک case برای when_type == 'instagram_comment' و action_type == 'instagram_comment_dm_reply' بذار.

⸻

اگر بخوام خیلی خلاصه بگم 👇
	•	مشکل فاجعه‌ای تو این دو فایل نمی‌بینم که معماری‌مون رو خراب کنه.
	•	چندتا نقطه اتصال هست که باید در فایل‌های دیگه (TriggerService, WorkflowExecutionService, InstagramService) تمیز بشه.
	•	همین فایل اینستاگرام فقط یک باگ واضح داره (دو تا _download_profile_picture) و چند تا TODO (متدهای instagram_service و ساختار واقعی comment webhook).




models.py


خیلی تمیز جمعش کردی 👏
بیام خط‌به‌خط فقط چک کنم ببینیم چیزی جا نمونده قبل از این‌که بدی دست Cursor.

⸻

✅ چیزهایی که الان کاملاً درست و هم‌راستا با صحبت‌هامونه

1️⃣ تریگر / اکشن / نود جدید اینستاگرام 👌
	•	تو Trigger.TRIGGER_TYPE_CHOICES:

('INSTAGRAM_COMMENT', 'Instagram Comment'),

✔ همونه که لازم داشتیم برای لاگ کامنت اینستاگرام.

	•	تو Action.ACTION_TYPE_CHOICES:

('instagram_comment_dm_reply', 'Instagram Comment → DM + Reply'),

✔ اکشن جدید برای دایرکت + ریپلای روی کامنت درست تعریف شده.

	•	تو WhenNode.WHEN_TYPE_CHOICES:

('instagram_comment', 'Instagram Comment'),

✔ نود “وقتی کامنت اینستاگرام” برای node-based workflow هم تعریف شده.

	•	تو ActionNode.ACTION_TYPE_CHOICES:

('instagram_comment_dm_reply', 'Instagram Comment → DM + Reply'),

✔ برای node-based اکشن هم اضافه شده.

2️⃣ فیلدهای مخصوص اینستاگرام روی WhenNode ✅

instagram_post_url = models.URLField(...)
instagram_media_type = models.CharField(...)
comment_keywords = models.JSONField(...)

این دقیقاً همون چیزیه که می‌خواستیم برای:
	•	فقط روی یک پست خاص (یا همه پست‌ها)
	•	فقط روی پست / ریل / ویدیو
	•	فقط وقتی کامنت حاوی فلان کلمه‌هاست

و تو save هم حواست بوده:

if self.comment_keywords is None:
    self.comment_keywords = []

خیلی خوبه 👌

3️⃣ فیلدهای اکشن اینستاگرام روی ActionNode ✅

instagram_dm_mode = STATIC | PRODUCT
instagram_dm_text_template
instagram_product_id
instagram_public_reply_enabled
instagram_public_reply_text

این دقیقاً مطابق همون سناریویی هست که با هم بستیم:
	•	حالت ۱: پیام ثابت
	•	حالت ۲: محصول انتخابی → هوش مصنوعی DM بسازد
	•	و اینکه:
	•	هم تو DM جواب بده
	•	هم کامنت را با یک متن ساده ریپلای کند (مثلاً: «قیمت رو دایرکت برات فرستادم»)

⸻

⚠ دو تا ایراد ریز ولی مهم (قبل از دادن فایل به Cursor)

الان مدل‌ها اوکی‌اند، ولی توی export/import بعضی فیلدهای جدیدت گم می‌شن 👇

1️⃣ Workflow.export_to_dict → نودهای When

الان این تیکه فقط اینا رو برای WhenNode export می‌کنه:

if hasattr(node, 'whennode'):
    when_node = node.whennode
    node_data.update({
        'when_type': when_node.when_type,
        'keywords': when_node.keywords,
        'tags': when_node.tags,
        'channels': when_node.channels,
        'schedule_frequency': when_node.schedule_frequency,
        'schedule_start_date': ...,
        'schedule_time': ...,
    })

❌ اما فیلدهای جدید اینستاگرام اینجا export نمی‌شن:
	•	instagram_post_url
	•	instagram_media_type
	•	comment_keywords

🔧 پیشنهاد: اینا رو هم اضافه کن:

if hasattr(node, 'whennode'):
    when_node = node.whennode
    node_data.update({
        'when_type': when_node.when_type,
        'keywords': when_node.keywords,
        'tags': when_node.tags,
        'channels': when_node.channels,
        'schedule_frequency': when_node.schedule_frequency,
        'schedule_start_date': when_node.schedule_start_date.isoformat() if when_node.schedule_start_date else None,
        'schedule_time': when_node.schedule_time.isoformat() if when_node.schedule_time else None,
        # ✅ اضافه‌های جدید
        'instagram_post_url': when_node.instagram_post_url,
        'instagram_media_type': when_node.instagram_media_type,
        'comment_keywords': when_node.comment_keywords,
    })

و در import_from_dict، تو بخش:

elif node_type == 'when':
    schedule_start_date = node_data.get('schedule_start_date')
    schedule_time = node_data.get('schedule_time')
    ...
    node = WhenNode.objects.create(
        **base_node_data,
        when_type=node_data.get('when_type', 'receive_message'),
        keywords=node_data.get('keywords', []),
        tags=node_data.get('tags', []),
        channels=node_data.get('channels', []),
        schedule_frequency=node_data.get('schedule_frequency'),
        schedule_start_date=schedule_start_date,
        schedule_time=schedule_time,
    )

اینجا هم باید اینا رو اضافه کنی:

    node = WhenNode.objects.create(
        **base_node_data,
        when_type=node_data.get('when_type', 'receive_message'),
        keywords=node_data.get('keywords', []),
        tags=node_data.get('tags', []),
        channels=node_data.get('channels', []),
        schedule_frequency=node_data.get('schedule_frequency'),
        schedule_start_date=schedule_start_date,
        schedule_time=schedule_time,
        # ✅ اضافه‌های جدید
        instagram_post_url=node_data.get('instagram_post_url'),
        instagram_media_type=node_data.get('instagram_media_type', 'all'),
        comment_keywords=node_data.get('comment_keywords', []),
    )

اگر این کار رو نکنی، وقتی ورک‌فلو export/import کنی، فیلترهای اینستاگرام پاک می‌شن.

⸻

2️⃣ Workflow.export_to_dict → نودهای Action

الان برای ActionNode فقط این‌ها export می‌شن:

elif hasattr(node, 'actionnode'):
    action_node = node.actionnode
    node_data.update({
        'action_type': action_node.action_type,
        'message_content': action_node.message_content,
        'delay_amount': action_node.delay_amount,
        'delay_unit': action_node.delay_unit,
        'redirect_destination': action_node.redirect_destination,
        'tag_name': action_node.tag_name,
        'webhook_url': action_node.webhook_url,
        'webhook_method': action_node.webhook_method,
        'webhook_headers': action_node.webhook_headers,
        'webhook_payload': action_node.webhook_payload,
        'custom_code': action_node.custom_code,
        'ai_control_action': action_node.ai_control_action,
        'ai_custom_prompt': action_node.ai_custom_prompt,
        'ai_context_data': action_node.ai_context_data,
    })

❌ ولی فیلدهای اینستاگرامی اینجا نیستن:
	•	instagram_dm_mode
	•	instagram_dm_text_template
	•	instagram_product_id
	•	instagram_public_reply_enabled
	•	instagram_public_reply_text

🔧 اینا رو هم اضافه کن:

elif hasattr(node, 'actionnode'):
    action_node = node.actionnode
    node_data.update({
        'action_type': action_node.action_type,
        'message_content': action_node.message_content,
        'delay_amount': action_node.delay_amount,
        'delay_unit': action_node.delay_unit,
        'redirect_destination': action_node.redirect_destination,
        'tag_name': action_node.tag_name,
        'webhook_url': action_node.webhook_url,
        'webhook_method': action_node.webhook_method,
        'webhook_headers': action_node.webhook_headers,
        'webhook_payload': action_node.webhook_payload,
        'custom_code': action_node.custom_code,
        'ai_control_action': action_node.ai_control_action,
        'ai_custom_prompt': action_node.ai_custom_prompt,
        'ai_context_data': action_node.ai_context_data,
        # ✅ اینستاگرام
        'instagram_dm_mode': action_node.instagram_dm_mode,
        'instagram_dm_text_template': action_node.instagram_dm_text_template,
        'instagram_product_id': str(action_node.instagram_product_id) if action_node.instagram_product_id else None,
        'instagram_public_reply_enabled': action_node.instagram_public_reply_enabled,
        'instagram_public_reply_text': action_node.instagram_public_reply_text,
    })

و تو import_from_dict، توی بخش elif node_type == 'action': هم باید اینا رو برگردونی:

elif node_type == 'action':
    node = ActionNode.objects.create(
        **base_node_data,
        action_type=node_data.get('action_type', 'send_message'),
        message_content=node_data.get('message_content', ''),
        delay_amount=node_data.get('delay_amount', 0),
        delay_unit=node_data.get('delay_unit', 'minutes'),
        redirect_destination=node_data.get('redirect_destination', ''),
        tag_name=node_data.get('tag_name', ''),
        webhook_url=node_data.get('webhook_url', ''),
        webhook_method=node_data.get('webhook_method', 'POST'),
        webhook_headers=node_data.get('webhook_headers', {}),
        webhook_payload=node_data.get('webhook_payload', {}),
        custom_code=node_data.get('custom_code', ''),
        ai_control_action=node_data.get('ai_control_action', ''),
        ai_custom_prompt=node_data.get('ai_custom_prompt', ''),
        ai_context_data=node_data.get('ai_context_data', {}),
        # ✅ اینستاگرام
        instagram_dm_mode=node_data.get('instagram_dm_mode', 'STATIC'),
        instagram_dm_text_template=node_data.get('instagram_dm_text_template', ''),
        instagram_product_id=node_data.get('instagram_product_id'),
        instagram_public_reply_enabled=node_data.get('instagram_public_reply_enabled', False),
        instagram_public_reply_text=node_data.get('instagram_public_reply_text', ''),
    )


⸻

✅ نتیجه: الان وضعیت این فایل چطوره؟
	•	از نظر مدل دیتابیس:
👉 برای قابلیت Instagram Comment → DM + Reply (هم legacy workflow، هم node-based)
تقریباً کامل و تمیزه ✔
	•	فقط لازم داری:
	•	📌 فیلدهای اینستاگرامی رو تو export/import هم اضافه کنی
(تا وقتی کاربر یک ورک‌فلو رو export/import می‌کنه، تنظیماتش نسوزه)

بعد از این دو تا اصلاح، با خیال راحت می‌تونی این فایل رو بدی به Cursor و بگی:

«فقط migration بساز و بعد طبق همین فیلدها، UI و سرویس‌های
instagram_comment_dm_reply رو پیاده کن.»

