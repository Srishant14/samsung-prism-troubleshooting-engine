"""
Pre-defined diagnostic decision trees for each domain.

These are NOT LLM-generated. They are structured, verified diagnostic paths
that narrow from broad symptoms to specific issues.

Each tree has:
- "entry_question": The first question to ask for this domain/symptom
- Additional nodes: Follow-up questions keyed by node name
- Each option either:
  - "narrows_to": resolves to a specific {domain, issue}
  - "sets_context": adds context to the current issue
  - "follow_up": points to the next question node
"""
from typing import Dict, Any, Optional, List


# ============================================================
# Diagnostic Tree Definitions
# ============================================================

DIAGNOSTIC_TREES: Dict[str, Dict[str, Any]] = {

    # --------------------------------------------------------
    # BATTERY DOMAIN
    # --------------------------------------------------------
    "battery": {
        "entry_question": {
            "text": "What best describes your battery issue?",
            "options": [
                {
                    "label": "Battery drains very quickly",
                    "narrows_to": {"domain": "battery", "issue": "fast_drain"},
                    "follow_up": "fast_drain_context"
                },
                {
                    "label": "Phone charges slowly",
                    "narrows_to": {"domain": "battery", "issue": "slow_charging"}
                },
                {
                    "label": "Phone gets hot while charging",
                    "narrows_to": {"domain": "battery", "issue": "overheating_while_charging"}
                },
                {
                    "label": "Battery percentage seems wrong or stuck",
                    "narrows_to": {"domain": "battery", "issue": "battery_percentage_stuck"}
                },
                {
                    "label": "Battery drains overnight or on standby",
                    "narrows_to": {"domain": "battery", "issue": "drain_overnight"}
                },
                {
                    "label": "Battery is physically swollen or bulging",
                    "narrows_to": {"domain": "battery", "issue": "battery_swelling"}
                },
            ]
        },
        "fast_drain_context": {
            "text": "When did the fast battery drain start?",
            "options": [
                {
                    "label": "After a software update",
                    "narrows_to": {"domain": "battery", "issue": "fast_drain"},
                    "sets_context": "after_update"
                },
                {
                    "label": "After installing a new app",
                    "narrows_to": {"domain": "battery", "issue": "fast_drain"},
                    "sets_context": "after_app_install"
                },
                {
                    "label": "It has been gradual / happening for a while",
                    "narrows_to": {"domain": "battery", "issue": "fast_drain"}
                },
            ]
        },
    },

    # --------------------------------------------------------
    # DISPLAY DOMAIN
    # --------------------------------------------------------
    "display": {
        "entry_question": {
            "text": "What's happening with your screen?",
            "options": [
                {
                    "label": "Screen is flickering or blinking",
                    "narrows_to": {"domain": "display", "issue": "screen_flicker"},
                    "follow_up": "flicker_context"
                },
                {
                    "label": "Touchscreen is not responding",
                    "narrows_to": {"domain": "display", "issue": "touch_unresponsive"}
                },
                {
                    "label": "Screen is too dim even at max brightness",
                    "narrows_to": {"domain": "display", "issue": "screen_too_dim"}
                },
                {
                    "label": "I see ghost images or burn-in",
                    "narrows_to": {"domain": "display", "issue": "screen_burn_in"}
                },
                {
                    "label": "Auto brightness is not adjusting properly",
                    "narrows_to": {"domain": "display", "issue": "auto_brightness_issue"}
                },
                {
                    "label": "Always-On Display is not showing",
                    "narrows_to": {"domain": "display", "issue": "always_on_display_fail"}
                },
            ]
        },
        "flicker_context": {
            "text": "When does the screen flicker?",
            "options": [
                {
                    "label": "All the time / randomly",
                    "narrows_to": {"domain": "display", "issue": "screen_flicker"}
                },
                {
                    "label": "When I change the brightness",
                    "narrows_to": {"domain": "display", "issue": "screen_flicker"},
                    "sets_context": "brightness_change"
                },
                {
                    "label": "After a software update",
                    "narrows_to": {"domain": "display", "issue": "screen_flicker"},
                    "sets_context": "after_update"
                },
            ]
        },
    },

    # --------------------------------------------------------
    # CAMERA DOMAIN
    # --------------------------------------------------------
    "camera": {
        "entry_question": {
            "text": "What's wrong with your camera?",
            "options": [
                {
                    "label": "Photos are blurry or out of focus",
                    "narrows_to": {"domain": "camera", "issue": "camera_blur"},
                    "follow_up": "blur_context"
                },
                {
                    "label": "Camera app keeps crashing",
                    "narrows_to": {"domain": "camera", "issue": "camera_app_crash"}
                },
                {
                    "label": "Camera shows a black screen",
                    "narrows_to": {"domain": "camera", "issue": "camera_black_screen"}
                },
                {
                    "label": "There's a delay when taking photos",
                    "narrows_to": {"domain": "camera", "issue": "camera_lag_shutter"}
                },
                {
                    "label": "Front/selfie camera quality is bad",
                    "narrows_to": {"domain": "camera", "issue": "front_camera_issue"}
                },
            ]
        },
        "blur_context": {
            "text": "When are your photos blurry?",
            "options": [
                {
                    "label": "All the time / in general",
                    "narrows_to": {"domain": "camera", "issue": "camera_blur"}
                },
                {
                    "label": "In low light or at night",
                    "narrows_to": {"domain": "camera", "issue": "blurry_night_photos"},
                    "sets_context": "low_light"
                },
                {
                    "label": "Only for close-up or macro shots",
                    "narrows_to": {"domain": "camera", "issue": "camera_blur"},
                    "sets_context": "close_up"
                },
            ]
        },
    },

    # --------------------------------------------------------
    # PERFORMANCE DOMAIN
    # --------------------------------------------------------
    "performance": {
        "entry_question": {
            "text": "What kind of performance issue are you experiencing?",
            "options": [
                {
                    "label": "Phone feels slow or laggy overall",
                    "narrows_to": {"domain": "performance", "issue": "app_lag"},
                    "follow_up": "lag_context"
                },
                {
                    "label": "Apps take a long time to open",
                    "narrows_to": {"domain": "performance", "issue": "slow_apps"}
                },
                {
                    "label": "Phone keeps freezing or hanging",
                    "narrows_to": {"domain": "performance", "issue": "phone_freezing"}
                },
                {
                    "label": "Apps keep crashing or force-closing",
                    "narrows_to": {"domain": "performance", "issue": "apps_crashing"}
                },
                {
                    "label": "Phone overheats during gaming",
                    "narrows_to": {"domain": "performance", "issue": "overheating_gaming"}
                },
                {
                    "label": "Phone takes too long to start up",
                    "narrows_to": {"domain": "performance", "issue": "slow_boot"}
                },
            ]
        },
        "lag_context": {
            "text": "When did the slowness start?",
            "options": [
                {
                    "label": "After a software update",
                    "narrows_to": {"domain": "performance", "issue": "app_lag"},
                    "sets_context": "after_update"
                },
                {
                    "label": "After installing a new app",
                    "narrows_to": {"domain": "performance", "issue": "app_lag"},
                    "sets_context": "after_app_install"
                },
                {
                    "label": "Storage is almost full",
                    "narrows_to": {"domain": "performance", "issue": "storage_full_slowdown"}
                },
                {
                    "label": "It's been gradual / happening for a while",
                    "narrows_to": {"domain": "performance", "issue": "app_lag"}
                },
            ]
        },
    },

    # --------------------------------------------------------
    # CROSS-DOMAIN: OVERHEATING
    # When the user says "my phone is overheating" without context
    # --------------------------------------------------------
    "overheating": {
        "entry_question": {
            "text": "When does your phone overheat?",
            "options": [
                {
                    "label": "While charging",
                    "narrows_to": {"domain": "battery", "issue": "overheating_while_charging"}
                },
                {
                    "label": "While gaming or using heavy apps",
                    "narrows_to": {"domain": "performance", "issue": "overheating_gaming"}
                },
                {
                    "label": "Even when idle or not using it much",
                    "follow_up": "idle_overheat"
                },
            ]
        },
        "idle_overheat": {
            "text": "Does the battery also drain unusually fast?",
            "options": [
                {
                    "label": "Yes, battery drains quickly too",
                    "narrows_to": {"domain": "battery", "issue": "fast_drain"}
                },
                {
                    "label": "No, battery life seems normal",
                    "narrows_to": {"domain": "performance", "issue": "app_lag"}
                },
            ]
        },
    },

    # --------------------------------------------------------
    # GENERAL: When domain itself is unclear
    # --------------------------------------------------------
    "general": {
        "entry_question": {
            "text": "Which area is most affected?",
            "options": [
                {
                    "label": "Battery or charging",
                    "follow_up": None,
                    "sets_tree": "battery"
                },
                {
                    "label": "Screen or display",
                    "follow_up": None,
                    "sets_tree": "display"
                },
                {
                    "label": "Camera or photos",
                    "follow_up": None,
                    "sets_tree": "camera"
                },
                {
                    "label": "Speed or performance",
                    "follow_up": None,
                    "sets_tree": "performance"
                },
            ]
        },
    },
}


# ============================================================
# Ambiguous query patterns that should trigger follow-up
# ============================================================

# Queries containing these patterns should get follow-up questions
# even if the classifier assigns a specific issue, because the
# user's description is broad enough that asking helps.
AMBIGUOUS_PATTERNS = {
    "overheating": {
        "keywords": ["overheat", "overheating", "overheats", "phone is hot", "phone gets hot", "phone heating up"],
        "tree": "overheating",
        "description": "Overheating could be battery, performance, or charging related"
    },
    "general_battery": {
        "keywords": ["battery problem", "battery issue", "battery trouble", "battery bad", "battery drain", "battery dying",
                     "something wrong with battery", "issue with battery"],
        "tree": "battery",
        "description": "Generic battery complaint without specific symptom"
    },
    "general_camera": {
        "keywords": ["camera problem", "camera issue", "camera not working", "camera bad",
                     "camera trouble", "something wrong with camera"],
        "tree": "camera",
        "description": "Generic camera complaint without specific symptom"
    },
    "general_display": {
        "keywords": ["screen problem", "display issue", "screen not working", "screen bad",
                     "display trouble", "something wrong with screen",
                     "something wrong with display"],
        "tree": "display",
        "description": "Generic display complaint without specific symptom"
    },
    "general_performance": {
        "keywords": ["phone problem", "performance issue", "phone not right", "phone sucks", "phone bad",
                     "phone trouble", "phone slow", "phone lag", "phone freeze", "phone hang"],
        "tree": "performance",
        "description": "Generic performance complaint"
    },
}


def detect_ambiguous_pattern(query: str) -> Optional[str]:
    """
    Check if a query matches an ambiguous pattern that should trigger
    the diagnostic flow instead of immediate classification.

    Returns the tree name to use, or None if query is specific enough.
    """
    query_lower = query.lower()
    for pattern_name, pattern in AMBIGUOUS_PATTERNS.items():
        for keyword in pattern["keywords"]:
            if keyword in query_lower:
                return pattern["tree"]
    return None


def get_question(tree_name: str, node_name: str) -> Optional[Dict]:
    """Get a question node from a diagnostic tree."""
    tree = DIAGNOSTIC_TREES.get(tree_name)
    if not tree:
        return None
    return tree.get(node_name)


def apply_option(tree_name: str, node_name: str, option_index: int) -> Dict[str, Any]:
    """
    Apply a user's selected option and determine the next step.

    Returns a dict with:
    - "resolved": True if we have a final domain/issue
    - "domain", "issue", "context": the resolved classification (if resolved)
    - "next_tree", "next_node": the next question to ask (if not resolved)
    - "sets_tree": if this option switches to a different tree
    """
    question = get_question(tree_name, node_name)
    if not question or option_index >= len(question["options"]):
        return {"resolved": False, "error": "Invalid question or option"}

    option = question["options"][option_index]
    result: Dict[str, Any] = {"resolved": False}

    # Check if this option switches to a different tree entirely
    if "sets_tree" in option and option["sets_tree"]:
        result["next_tree"] = option["sets_tree"]
        result["next_node"] = "entry_question"
        return result

    # Check if this option resolves to a specific issue
    if "narrows_to" in option and option["narrows_to"]:
        result["domain"] = option["narrows_to"].get("domain")
        result["issue"] = option["narrows_to"].get("issue")

    # Check if this option sets a context
    if "sets_context" in option and option["sets_context"]:
        result["context"] = option["sets_context"]

    # Check if there's a follow-up question
    if "follow_up" in option and option["follow_up"]:
        result["next_node"] = option["follow_up"]
        result["next_tree"] = tree_name  # stay in same tree
        result["resolved"] = False
    elif result.get("domain") and result.get("issue"):
        result["resolved"] = True
    else:
        # Option with no follow-up and no narrows_to — shouldn't happen
        result["resolved"] = False

    return result


def get_entry_tree_for_domain(domain: str) -> Optional[str]:
    """Get the diagnostic tree name for a given domain."""
    if domain in DIAGNOSTIC_TREES:
        return domain
    return None
