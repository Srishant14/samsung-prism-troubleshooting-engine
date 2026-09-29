import json
import re
from typing import List
from google import genai

from config import GEMINI_API_KEY, LLM_TIMEOUT
from schemas import IssueClassification, LLMClassification
from logger import log_classification

# Initialize Gemini client if API key is provided
client = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """You are a device issue classifier for Samsung's Smart Troubleshooting Engine.

Your ONLY job is to classify the user's complaint into structured issues.
You must NOT generate troubleshooting steps, advice, or deep links.

OUTPUT FORMAT — strict JSON only:
{
  "issues": [
    {
      "domain": "<domain>",
      "issue": "<issue_identifier>",
      "context": "<optional_context_or_null>",
      "confidence": <float_0_to_1>
    }
  ]
}

SUPPORTED TAXONOMY — you may ONLY use these domain/issue combinations:

battery:
  - fast_drain: battery draining quickly, poor battery life, phone dies fast
  - slow_charging: phone charges slowly
  - overheating_while_charging: phone gets hot while charging
  - battery_percentage_stuck: battery percentage not updating correctly
  - drain_overnight: battery drains during sleep/standby
  - battery_swelling: physical battery swelling or bulging

display:
  - screen_flicker: screen flickering, blinking, flashing, visual glitches
  - auto_brightness_issue: adaptive/auto brightness not working
  - touch_unresponsive: touchscreen not responding
  - screen_burn_in: ghost images, burn-in on screen
  - always_on_display_fail: AOD not working
  - screen_too_dim: screen too dark

camera:
  - camera_blur: blurry photos (general)
  - camera_app_crash: camera app crashing or failing
  - blurry_night_photos: blurry photos specifically in low light
  - camera_lag_shutter: shutter delay when taking photos
  - front_camera_issue: front/selfie camera quality problems
  - camera_black_screen: camera shows black screen

performance:
  - app_lag: phone feels slow or laggy in general
  - slow_apps: apps specifically take long to open/load
  - phone_freezing: phone keeps freezing or locking up
  - storage_full_slowdown: phone slow due to low storage
  - overheating_gaming: phone overheats during gaming
  - apps_crashing: apps keep force-closing
  - slow_boot: phone takes long to start up

CONTEXT values (optional, use when the user specifies a condition):
  - "after_update" — issue started after a software update
  - "after_app_install" — issue started after installing an app
  - "brightness_change" — happens when changing brightness
  - "low_light" / "night" — in dark/low-light conditions
  - "gaming" — during heavy gaming
  - "charging" — while charging
  - "overnight" / "idle" / "standby" — during sleep/idle
  - null — no specific context mentioned

CLASSIFICATION RULES:

1. Understand MEANING, not just keywords. These all mean battery/fast_drain:
   - "My phone barely lasts half a day"
   - "Battery backup is terrible"
   - "Phone doesn't last through the day"
   - "bro my battery is literally dying in 3 hours"
   - "My phone dies way too quickly"

2. These all mean performance/app_lag or performance/slow_apps:
   - "Everything feels laggy"
   - "Apps are taking forever to open"
   - "My phone has become very slow"
   - "Phone stutters when scrolling"

3. These mean display/screen_flicker:
   - "Display flashes randomly"
   - "My screen keeps blinking"
   - "Screen glitches and flickers"

4. If the user describes MULTIPLE independent problems, return MULTIPLE issues:
   - "My screen is flickering and my battery is draining fast"
     → TWO issues: display/screen_flicker AND battery/fast_drain
   - "My phone is slow and battery drains quickly"
     → TWO issues: performance/app_lag AND battery/fast_drain

5. If the query is vague, ambiguous, or not about a device problem:
   - "My phone is not working properly" → confidence < 0.3
   - "It's getting worse" → confidence < 0.3
   - "Can you fix my phone?" → confidence < 0.3
   Return: {"issues": [{"domain": "unknown", "issue": "unknown", "context": null, "confidence": 0.1}]}

6. If the issue has a SPECIFIC context not covered by the taxonomy (e.g., "camera blurry only for close-up photos"), classify with the closest domain/issue but set a LOWER confidence (0.5-0.6) to indicate partial match. Set context to describe the specific condition (e.g., "close_up").

7. Do NOT invent issues outside the taxonomy above.
8. Do NOT generate troubleshooting steps.
9. Do NOT generate deep links.
10. Output ONLY valid JSON. No markdown, no explanation.
"""


def _has_word(query_lower: str, word: str) -> bool:
    """Check if word appears as a whole word (not as substring of another word)."""
    import re
    return bool(re.search(r'\b' + re.escape(word) + r'\b', query_lower))


def _has_any_word(query_lower: str, words: list) -> bool:
    """Check if any word from the list appears as a whole word."""
    return any(_has_word(query_lower, w) for w in words)


def _has_any_phrase(query_lower: str, phrases: list) -> bool:
    """Check if any phrase appears in the query (substring match, for multi-word phrases)."""
    return any(p in query_lower for p in phrases)


def simple_keyword_fallback(query: str) -> LLMClassification:
    """
    Fallback classification when LLM is unavailable.
    Uses keyword matching to identify domain + specific issue.
    Returns issues list format. Supports detecting two issues.
    """
    query_lower = query.lower()
    issues: List[IssueClassification] = []

    # --- Battery detection ---
    battery_signals = ["battery", "charge", "drain", "power", "dying", "backup",
                       "lasts", "last all day", "last half", "dies", "hours of battery",
                       "runs out", "loses charge", "lose charge", "overheat", "overheating", "overheats",
                       "heating", "heats", "warm", "temperature"]
    if _has_any_word(query_lower, battery_signals) or any(phrase in query_lower for phrase in ["battery drain", "loses charge"]):
        context = None
        if any(w in query_lower for w in ["update", "updated", "latest version"]):
            context = "after_update"
        elif any(w in query_lower for w in ["app", "install"]):
            context = "after_app_install"

        if any(word in query_lower for word in ["slow charge", "takes forever to charge", "charging slow", "charges slowly"]):
            issues.append(IssueClassification(domain="battery", issue="slow_charging", context=context, confidence=0.7))
        elif _has_any_word(query_lower, ["hot", "overheat", "overheating", "overheats", "warm", "heating", "heats"]):
            issues.append(IssueClassification(domain="battery", issue="overheating_while_charging", context=context, confidence=0.7))
        elif any(word in query_lower for word in ["stuck", "percent", "percentage not"]):
            issues.append(IssueClassification(domain="battery", issue="battery_percentage_stuck", context=context, confidence=0.7))
        elif any(word in query_lower for word in ["overnight", "sleep", "standby", "idle"]):
            issues.append(IssueClassification(domain="battery", issue="drain_overnight", context=context, confidence=0.7))
        elif any(word in query_lower for word in ["swell", "bulg", "expand", "popping"]):
            issues.append(IssueClassification(domain="battery", issue="battery_swelling", context=context, confidence=0.7))
        else:
            issues.append(IssueClassification(domain="battery", issue="fast_drain", context=context, confidence=0.7))

    # --- Display detection ---
    display_signals = ["screen", "display", "brightness", "flicker", "touch", "dim",
                       "blink", "flash", "glitch"]
    if _has_any_word(query_lower, display_signals):
        context = None
        if any(w in query_lower for w in ["brightness"]):
            context = "brightness_change"

        if any(word in query_lower for word in ["flicker", "blink", "glitch", "flash"]):
            issues.append(IssueClassification(domain="display", issue="screen_flicker", context=context, confidence=0.7))
        elif any(word in query_lower for word in ["brightness", "adaptive", "auto bright"]):
            issues.append(IssueClassification(domain="display", issue="auto_brightness_issue", context=context, confidence=0.7))
        elif any(word in query_lower for word in ["touch", "respond", "tap", "unresponsive"]):
            issues.append(IssueClassification(domain="display", issue="touch_unresponsive", context=context, confidence=0.7))
        elif any(word in query_lower for word in ["burn", "ghost", "faint image"]):
            issues.append(IssueClassification(domain="display", issue="screen_burn_in", context=context, confidence=0.7))
        elif any(word in query_lower for word in ["always on", "aod", "clock"]):
            issues.append(IssueClassification(domain="display", issue="always_on_display_fail", context=context, confidence=0.7))
        elif any(word in query_lower for word in ["dim", "dark", "can't see"]):
            issues.append(IssueClassification(domain="display", issue="screen_too_dim", context=context, confidence=0.7))
        elif not issues:  # Only add generic display if no other issue matched
            issues.append(IssueClassification(domain="display", issue="screen_flicker", context=context, confidence=0.7))

    # --- Camera detection ---
    camera_signals = ["camera", "photo", "picture", "lens", "blur", "selfie", "fuzzy"]
    if _has_any_word(query_lower, camera_signals) or any(p in query_lower for p in ["close-up", "close up"]):
        if any(word in query_lower for word in ["close-up", "close up", "macro", "closeup"]):
            issues.append(IssueClassification(domain="camera", issue="camera_blur", context="close_up", confidence=0.5))
        elif any(word in query_lower for word in ["crash", "force close", "error", "failed", "closes"]):
            issues.append(IssueClassification(domain="camera", issue="camera_app_crash", context=None, confidence=0.7))
        elif any(word in query_lower for word in ["night", "dark", "low light"]):
            issues.append(IssueClassification(domain="camera", issue="blurry_night_photos", context="low_light", confidence=0.7))
        elif any(word in query_lower for word in ["lag", "delay", "shutter"]):
            issues.append(IssueClassification(domain="camera", issue="camera_lag_shutter", context=None, confidence=0.7))
        elif any(word in query_lower for word in ["front", "selfie"]):
            issues.append(IssueClassification(domain="camera", issue="front_camera_issue", context="front_camera", confidence=0.7))
        elif any(word in query_lower for word in ["black screen", "black", "viewfinder"]):
            issues.append(IssueClassification(domain="camera", issue="camera_black_screen", context=None, confidence=0.7))
        elif any(word in query_lower for word in ["close-up", "close up", "macro"]):
            issues.append(IssueClassification(domain="camera", issue="camera_blur", context="close_up", confidence=0.5))
        else:
            issues.append(IssueClassification(domain="camera", issue="camera_blur", context=None, confidence=0.7))

    # --- Performance detection ---
    perf_signals = ["slow", "lag", "freeze", "crash", "hot", "heat", "heats", "heating", "overheat", "overheating", "hang", "hangs",
                    "forever", "loading", "sluggish", "stutters", "laggy"]
    if _has_any_word(query_lower, perf_signals) and not any(
        i.domain in ("battery", "camera") and i.issue in ("slow_charging",) for i in issues
    ):
        context = None
        if any(w in query_lower for w in ["update", "updated"]):
            context = "after_update"
        elif any(w in query_lower for w in ["install", "new app"]):
            context = "after_app_install"

        # Check if we already have a performance issue
        has_perf = any(i.domain == "performance" for i in issues)
        if not has_perf:
            if any(word in query_lower for word in ["freeze", "frozen", "lock", "hang", "hangs"]):
                issues.append(IssueClassification(domain="performance", issue="phone_freezing", context=context, confidence=0.7))
            elif any(word in query_lower for word in ["storage", "space", "memory full"]):
                issues.append(IssueClassification(domain="performance", issue="storage_full_slowdown", context=context, confidence=0.7))
            elif any(word in query_lower for word in ["gaming", "game"]) and any(w in query_lower for w in ["hot", "heat", "heats", "overheat", "overheating"]):
                issues.append(IssueClassification(domain="performance", issue="overheating_gaming", context="gaming", confidence=0.7))
            elif any(word in query_lower for word in ["crash", "force close", "closing"]):
                issues.append(IssueClassification(domain="performance", issue="apps_crashing", context=context, confidence=0.7))
            elif any(word in query_lower for word in ["boot", "start", "turn on", "restart"]):
                issues.append(IssueClassification(domain="performance", issue="slow_boot", context=context, confidence=0.7))
            elif any(word in query_lower for word in ["app", "apps", "open", "loading", "forever"]):
                issues.append(IssueClassification(domain="performance", issue="slow_apps", context=context, confidence=0.7))
            else:
                issues.append(IssueClassification(domain="performance", issue="app_lag", context=context, confidence=0.7))

    # No match at all
    if not issues:
        issues.append(IssueClassification(domain="unknown", issue="unknown", context=None, confidence=0.1))

    # Deduplicate — remove issues with same domain+issue
    seen = set()
    unique_issues = []
    for issue in issues:
        key = (issue.domain, issue.issue)
        if key not in seen:
            seen.add(key)
            unique_issues.append(issue)

    return LLMClassification(issues=unique_issues)


def extract_json_from_response(text: str) -> str:
    """Extracts JSON string from markdown code blocks if present."""
    match = re.search(r'```(?:json)?(.*?)```', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


def classify_complaint(query: str) -> LLMClassification:
    """
    Classifies a user query into one or more domain/issue pairs using Gemini LLM.
    Falls back to keyword matching if LLM fails.
    """
    if not client:
        result = simple_keyword_fallback(query)
        log_classification(query, result)
        return result

    candidate_models = ['gemini-3.8-flash', 'gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-2.0-flash']
    for model_name in candidate_models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[
                    {"role": "user", "parts": [{"text": SYSTEM_PROMPT + f"\n\nUser query: {query}"}]}
                ],
                config={"http_options": {"timeout": LLM_TIMEOUT * 1000}},
            )

            response_text = extract_json_from_response(response.text)
            data = json.loads(response_text)

            raw_issues = data.get("issues", [])
            if not raw_issues:
                if "domain" in data:
                    raw_issues = [data]

            issues = []
            for item in raw_issues:
                issues.append(IssueClassification(
                    domain=item.get("domain", "unknown"),
                    issue=item.get("issue", "unknown"),
                    context=item.get("context"),
                    confidence=float(item.get("confidence", 0.1))
                ))

            if not issues:
                issues.append(IssueClassification(
                    domain="unknown", issue="unknown", context=None, confidence=0.1
                ))

            result = LLMClassification(issues=issues)
            log_classification(query, result)
            return result  # Success — break out of the model loop
        except Exception as e:
            print(f"LLM Classification attempt with model {model_name} failed: {e}")

    result = simple_keyword_fallback(query)
    log_classification(query, result)
    return result
