# 🧠 FIKO AI – Persona Extractor & Tone Adapter Layer
> Version 1.0 — for integration in `instagram_module` and AI core pipeline

---

## 🎯 GOAL
Enhance personalization by:
1. Extracting basic user persona info from Instagram Graph API (bio, username, followers)
2. Adjusting tone and context of AI responses dynamically (based on extracted interests, tone, and business context)

---

## ⚙️ 1. PERSONA EXTRACTOR (Instagram Graph API Only)

### 🔸 Source
Use **Instagram Business Graph API** - not Facebook Graph
Fetch only these fields:

```python
fields = [
    "id",
    "username",
    "name",
    "biography",
    "followers_count",
    "follows_count",
    "media_count"
]
```

### 🔸 Example Response
```json
{
  "id": "17841400008460056",
  "username": "coffee_and_camping",
  "name": "Omid Ataei",
  "biography": "Coffee lover ☕ | Camping & Travel | Outdoor espresso addicted",
  "followers_count": 2412,
  "follows_count": 325,
  "media_count": 58
}
```

### 🔸 Extraction Logic
Minimal NLP or Regex - lightweight, local only:
```python
import re

def extract_persona_from_bio(bio: str) -> dict:
    if not bio:
        return {"interests": [], "tone_preference": "neutral", "profession": None}
    
    interests = []
    keywords = ["coffee", "camping", "travel", "fitness", "fashion", "tech", "photography", "food"]
    for k in keywords:
        if re.search(k, bio.lower()):
            interests.append(k)
    
    tone_preference = "friendly" if any(i in bio.lower() for i in ["☕", "😊", "❤️", "😎"]) else "neutral"
    
    profession = None
    if "founder" in bio.lower() or "ceo" in bio.lower():
        profession = "entrepreneur"
    elif "designer" in bio.lower():
        profession = "designer"
    elif "coach" in bio.lower():
        profession = "coach"
    
    return {
        "interests": interests,
        "tone_preference": tone_preference,
        "profession": profession
    }
```

### 🔸 Example Output
```json
{
  "interests": ["coffee", "camping", "travel"],
  "tone_preference": "friendly",
  "profession": "entrepreneur"
}
```

### 🔸 Storage / Access
- If `conversation.platform == "instagram"`, call this extractor during **user context initialization**
- Add results to existing `user_context` object:
```python
user_context["persona"] = extract_persona_from_bio(bio)
```
- Never fail if `bio` is empty or unavailable:
```python
bio = instagram_user.get("biography", "")
persona = extract_persona_from_bio(bio)
```
- For Telegram or WhatsApp: set persona to default:
```python
persona = {"interests": [], "tone_preference": "neutral", "profession": None}
```

---

## 🗣️ 2. TONE ADAPTER LAYER

This layer modifies AI prompts or system context based on extracted persona.
It should be called **right before building the final AI prompt** or **inside `_build_prompt()`**.

### 🔸 Template Prompt Injection
Append this section to the top of the system prompt:

```python
def tone_instruction_from_persona(persona: dict, user_name: str = None) -> str:
    name_part = f"User name: {user_name}.\n" if user_name else ""
    interests_part = ", ".join(persona.get("interests", [])) or "none"
    tone = persona.get("tone_preference", "neutral")
    profession = persona.get("profession") or "unknown"

    return f"""
{name_part}
Persona detected:
- Profession: {profession}
- Interests: {interests_part}
- Tone preference: {tone}

Tone and response adaptation rules:
1. Maintain {tone} tone when responding.
2. If user interests include camping, coffee, photography, or travel, mention relevant products naturally.
3. Use user's first name if available (e.g., 'Omid, this model suits your travel style.').
4. Keep tone professional and brand-aligned; never overuse emojis.
"""
```

### 🔸 Example Integration
In `_build_prompt()` or `generate_response()`:
```python
prompt_parts = []

# Add persona/tone info (if available)
persona = user_context.get("persona", {})
tone_prompt = tone_instruction_from_persona(persona, user_context.get("name"))
prompt_parts.append(tone_prompt)

# Then add main system instructions and knowledge context
prompt_parts.append(core_instruction)
prompt_parts.append(context_from_RAG)

final_prompt = "\n".join(prompt_parts)
```

---

## ⚠️ Edge Cases
| Platform | Available Data | Behavior |
|-----------|----------------|-----------|
| **Instagram** | bio, username, follower counts | Persona extraction active ✅ |
| **Telegram / WhatsApp / Web** | only name or ID | Persona defaults to neutral |
| **Empty bio or API error** | - | Fallback: neutral tone, no personalization |
| **User changed bio mid-chat** | update only on next session init |

---

## ✅ Benefits
- Personalization without fine-tuning the LLM
- Context-aware tone per user (friendly, formal, expert)
- Lightweight and fully GDPR-compliant
- Safe fallback (no crash if bio is missing)

---

**Author:** FIKO AI Labs LTD  
**Date:** 2025-10-10  
**Version:** 1.0
