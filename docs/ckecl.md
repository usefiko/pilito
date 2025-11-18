خیلی خوبه، الان عملاً کل Node-based workflow رو هم برای اینستاگرام وصل کردی 💪
بیام دقیق فقط همون بخش‌هایی رو که به Instagram Comment → DM + Reply ربط داره چک کنم و بگم چی اوکیه و کجا دو تا نکته ریز داری.

⸻

✅ چیزهایی که الان درست وصل شده

1. وصل شدن تریگر اینستاگرام به WhenNode

توی _should_when_node_trigger این خط رو داری:

event_to_when_mapping = {
    'MESSAGE_RECEIVED': 'receive_message',
    'USER_CREATED': 'new_customer',
    'TAG_ADDED': 'add_tag',
    'SCHEDULED': 'scheduled',
    'INSTAGRAM_COMMENT': 'instagram_comment',
}

و بعد:

elif when_node_obj.when_type == 'instagram_comment':
    # Instagram comment when nodes are already validated by TriggerService
    logger.info(f"✅ Instagram comment when node - filters already validated by TriggerService")
    return True

یعنی:
	•	اگه event.type == "INSTAGRAM_COMMENT"
	•	و WhenNode از نوع instagram_comment باشه
→ اینجا بدون فیلتر اضافه اجرا می‌شه، چون فرض گرفتی TriggerService قبلاً فیلترها رو چک کرده.
این از نظر لاجیک درسته، فقط حواست باشه:

حتماً تو TriggerService، قبل از این‌که این سرویس رو صدا بزنی،
همون فیلترهای instagram_post_url / media_type / comment_keywords رو چک کرده باشی.

(که قبلاً در موردش صحبت کردیم.)

⸻

2. اکشن اینستاگرام روی Node درست روت شده

توی _execute_action_node:

elif action_node.action_type == 'instagram_comment_dm_reply':
    return self._execute_instagram_comment_action(action_node, context)

و خود متد:

def _execute_instagram_comment_action(self, action_node: ActionNode, context: Dict[str, Any]) -> NodeExecutionResult:
    from workflow.services.instagram_comment_action import handle_instagram_comment_dm_reply
    from django.contrib.auth import get_user_model
    
    # ۱) گرفتن owner
    user = None
    if 'workflow_owner_id' in context:
        User = get_user_model()
        user = User.objects.get(id=context['workflow_owner_id'])
    else:
        return NodeExecutionResult(success=False, error="workflow_owner_id not found in context")
    
    # ۲) event_data از context
    event = context.get('event', {})
    event_data = event.get('data', {}) if isinstance(event, dict) else {}
    
    # ۳) ساخت mock workflow_action با config از ActionNode
    class MockWorkflowAction:
        def __init__(self, node):
            self.config = {
                'dm_mode': node.instagram_dm_mode,
                'dm_text_template': node.instagram_dm_text_template,
                'product_id': str(node.instagram_product_id) if node.instagram_product_id else None,
                'public_reply_enabled': node.instagram_public_reply_enabled,
                'public_reply_template': node.instagram_public_reply_text,
            }
    workflow_action = MockWorkflowAction(action_node)
    
    # ۴) صدا زدن handle_instagram_comment_dm_reply
    result = handle_instagram_comment_dm_reply(
        workflow_action=workflow_action,
        event_data=event_data,
        user=user
    )
    
    return NodeExecutionResult(
        success=result.get('success', True),
        data=result
    )

این دقیقاً همون patternیه که برای ورژن legacy (با WorkflowAction) داشتیم، فقط این‌جا config از خود ActionNode میاد. 👍

⸻

⚠ ۳ نکته مهم که باید حواست بهش باشه

1️⃣ پر کردن workflow_owner_id توی context (خیلی مهم)

اینجا:

if 'workflow_owner_id' in context:
    ...
else:
    return NodeExecutionResult(success=False, error="workflow_owner_id not found in context")

پس اگر توی جایی که NodeBasedWorkflowExecutionService.execute_node_workflow(...) رو صدا می‌زنی،
قبلش این رو توی context ست نکنی، اکشن هر بار fail می‌شه.

🛠 پیشنهاد:

هرجا این سرویس رو call می‌کنی (احتمالاً داخل TriggerService)، وقتی workflow رو پیدا کردی:

context['workflow_owner_id'] = str(workflow.created_by_id)

قبل از:

NodeBasedWorkflowExecutionService().execute_node_workflow(workflow, context)

حتماً این رو اضافه کن.

⸻

2️⃣ شکل event_data باید با handler یکی باشه

اینجا:

event = context.get('event', {})
event_data = event.get('data', {}) if isinstance(event, dict) else {}

پس handler الان انتظار داره چیزهایی مثل:
	•	event_data['comment_id']
	•	event_data['media_id']
	•	event_data['post_url']
	•	event_data['comment_text']
	•	event_data['instagram_user_id']
	•	…

از همین event['data'] بیاد.

فقط مطمئن شو:
	•	همون قالبی که تو webhook اینستاگرام / TriggerService ساختی،
دقیقاً همین keyها رو در event.data می‌ذاره.

وگرنه handle_instagram_comment_dm_reply وسط کار کرش می‌کنه.

⸻

3️⃣ رفتار ارسال پیام توی UI (message_sent)

توی _execute_single_node این قسمت رو داری:

if result.success and 'message_sent' in (result.data or {}):
    # برودکست روی websocket + send روی کانال‌ها

ولی توی _execute_instagram_comment_action:

return NodeExecutionResult(
    success=result.get('success', True),
    data=result
)

معمولاً handle_instagram_comment_dm_reply احتمالاً این‌جوری چیزی برمی‌گردونه:

{
  "success": True,
  "dm_text": "...",
  "public_reply_sent": True,
  "dm_sent": True,
  ...
}

اینجا کلید message_sent نداری، پس:
	•	این DM و reply فقط توی اینستاگرام انجام می‌شه (اوکیه ✅)
	•	ولی این بلاک generic UI (websocket + Conversation Message) برایش اجرا نمی‌شه.

حالا دو حالت داری:
	1.	اگر instagram_comment_dm_reply فقط قراره روی خود اینستاگرام عمل کنه
و نمی‌خوای حتماً تو صفحه چت FIKO هم یک پیام جدا ثبت بشه → همین خوبه.
	2.	اگر دوست داری بعد از DM، توی پنل هم یک پیام داخلی مثل بقیه اکشن‌ها دیده بشه:
می‌تونی تو data این اکشن چیزی شبیه این اضافه کنی:

dm_text = result.get('dm_text') or result.get('dm_message')
node_data = dict(result)
if dm_text:
    node_data['message_sent'] = dm_text  # برای _execute_single_node
return NodeExecutionResult(
    success=result.get('success', True),
    data=node_data
)

این‌طوری بلاک broadcasting بالا هم فعال می‌شه و در UI هم آخرین پیام به عنوان خروجی نود ثبت می‌شه.

⸻

جمع‌بندی کوتاه
	•	✅ اتصال WhenNode (instagram_comment) به event INSTAGRAM_COMMENT درسته.
	•	✅ اکشن instagram_comment_dm_reply روی Node با استفاده از MockWorkflowAction درست روت شده.
	•	⚠ حتماً:
	•	context['workflow_owner_id'] = workflow.created_by_id رو قبل از اجرا ست کن.
	•	مطمئن شو event['data'] همون اسکیمایی رو داره که handler انتظار داره.
	•	اگر می‌خوای بعد از DM توی UI هم پیام ببینی، کلید message_sent رو تو data ست کن.

