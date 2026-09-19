"""
Gemini model definitions, context window specifications, and Free Tier rate limits.
"""

from typing import Dict, Any, List

AVAILABLE_MODELS: Dict[str, Dict[str, Any]] = {
    "gemini-2.0-flash": {
        "name": "Gemini 2.0 Flash",
        "description": "Флагманская модель нового поколения: непревзойденная скорость, высокое качество кода и рассуждений. Рекомендуется по умолчанию.",
        "description_en": "Next-generation flagship: blazing fast generation speed, high coding & reasoning accuracy. Recommended default.",
        "max_rpm": 15,
        "max_rpd": 1500,
        "max_tpm": 1_000_000,
        "context_window": 1_048_576,
        "is_default": True,
        "category": "Recommended / Flagship",
    },
    "gemini-2.0-flash-lite": {
        "name": "Gemini 2.0 Flash Lite",
        "description": "Сверхбыстрая и экономичная модель с минимальной задержкой и повышенным лимитом 30 RPM.",
        "description_en": "Ultra-fast and cost-efficient model with minimal latency and higher 30 RPM limit.",
        "max_rpm": 30,
        "max_rpd": 1500,
        "max_tpm": 4_000_000,
        "context_window": 1_048_576,
        "is_default": False,
        "category": "Fast & Lightweight",
    },
    "gemini-2.0-pro-exp-02-05": {
        "name": "Gemini 2.0 Pro Experimental",
        "description": "Лучшая модель Google для сложнейшего кодинга, проектирования архитектуры и глубокого рефакторинга.",
        "description_en": "Google's premiere model for complex coding, project architecture, and deep refactoring.",
        "max_rpm": 2,
        "max_rpd": 50,
        "max_tpm": 32_000,
        "context_window": 2_097_152,
        "is_default": False,
        "category": "Reasoning & Coding",
    },
    "gemini-2.0-flash-thinking-exp-01-21": {
        "name": "Gemini 2.0 Flash Thinking",
        "description": "Модель с глубоким пошаговым рассуждением (Chain-of-Thought) перед формулированием ответа.",
        "description_en": "Deep reasoning model with step-by-step thinking (Chain-of-Thought).",
        "max_rpm": 10,
        "max_rpd": 1500,
        "max_tpm": 1_000_000,
        "context_window": 1_048_576,
        "is_default": False,
        "category": "Thinking / Reasoning",
    },
    "gemini-1.5-pro": {
        "name": "Gemini 1.5 Pro",
        "description": "Классическая Pro-модель с огромным контекстом 2 миллиона токенов.",
        "description_en": "Classic Pro model with massive 2M token context window.",
        "max_rpm": 2,
        "max_rpd": 50,
        "max_tpm": 32_000,
        "context_window": 2_097_152,
        "is_default": False,
        "category": "Legacy Flagship",
    },
    "gemini-1.5-flash": {
        "name": "Gemini 1.5 Flash",
        "description": "Проверенная временем базовая модель с окном в 1 миллион токенов.",
        "description_en": "Time-tested base model with 1M token context window.",
        "max_rpm": 15,
        "max_rpd": 1500,
        "max_tpm": 1_000_000,
        "context_window": 1_048_576,
        "is_default": False,
        "category": "Legacy Workhorse",
    },
    "gemini-1.5-flash-8b": {
        "name": "Gemini 1.5 Flash 8B",
        "description": "Компактная быстрая модель для простых задач и частых запросов.",
        "description_en": "Compact fast model for high-frequency lightweight tasks.",
        "max_rpm": 15,
        "max_rpd": 1500,
        "max_tpm": 1_000_000,
        "context_window": 1_048_576,
        "is_default": False,
        "category": "Fast & Lightweight",
    },
}

# Aliases for convenience
MODEL_ALIASES: Dict[str, str] = {
    "flash": "gemini-2.0-flash",
    "pro": "gemini-2.0-pro-exp-02-05",
    "thinking": "gemini-2.0-flash-thinking-exp-01-21",
    "lite": "gemini-2.0-flash-lite",
    "2.0-flash": "gemini-2.0-flash",
    "2.0-lite": "gemini-2.0-flash-lite",
    "2.0-flash-lite": "gemini-2.0-flash-lite",
    "2.0-pro": "gemini-2.0-pro-exp-02-05",
    "2.0-thinking": "gemini-2.0-flash-thinking-exp-01-21",
    "gemini-2.0-pro": "gemini-2.0-pro-exp-02-05",
    "gemini-2.0-flash-thinking-exp": "gemini-2.0-flash-thinking-exp-01-21",
    "1.5-flash": "gemini-1.5-flash",
    "1.5-pro": "gemini-1.5-pro",
    "1.5-flash-8b": "gemini-1.5-flash-8b",
    # Legacy fallbacks in case stored config referenced previous names
    "gemini-2.5-flash": "gemini-2.0-flash",
    "gemini-2.5-pro": "gemini-2.0-pro-exp-02-05",
    "gemini-2.5-flash-thinking": "gemini-2.0-flash-thinking-exp-01-21",
    "2.5-flash": "gemini-2.0-flash",
    "2.5-pro": "gemini-2.0-pro-exp-02-05",
}

def resolve_model_id(model_id: str) -> str:
    """Resolve aliases and strip prefixes."""
    clean = model_id.strip().replace("models/", "")
    return MODEL_ALIASES.get(clean.lower(), clean)

def get_model_info(model_id: str) -> Dict[str, Any]:
    resolved = resolve_model_id(model_id)
    if resolved in AVAILABLE_MODELS:
        return AVAILABLE_MODELS[resolved]
    # Fallback default info for arbitrary custom model IDs from Google AI Studio
    return {
        "name": resolved,
        "description": f"Пользовательская модель: {resolved}",
        "description_en": f"Custom model: {resolved}",
        "max_rpm": 15,
        "max_rpd": 1500,
        "max_tpm": 1_000_000,
        "context_window": 1_048_576,
        "is_default": False,
        "category": "Custom",
    }

def register_dynamic_models(models_list: List[Dict[str, Any]]):
    """Register models fetched dynamically from Google AI Studio API."""
    for m in models_list:
        raw_name = m.get("name", "")
        clean_id = raw_name.replace("models/", "")
        if not clean_id or clean_id in AVAILABLE_MODELS:
            continue
        display_name = m.get("displayName", clean_id)
        desc = m.get("description", "")
        input_limit = m.get("inputTokenLimit", 1_048_576)
        AVAILABLE_MODELS[clean_id] = {
            "name": display_name,
            "description": desc or f"Модель из Google AI Studio: {display_name}",
            "description_en": desc or f"Google AI Studio model: {display_name}",
            "max_rpm": 15,
            "max_rpd": 1500,
            "max_tpm": 1_000_000,
            "context_window": input_limit,
            "is_default": False,
            "category": "AI Studio Live",
        }

def list_model_choices() -> List[Dict[str, Any]]:
    choices = []
    for mid, info in AVAILABLE_MODELS.items():
        choices.append({
            "id": mid,
            "name": info["name"],
            "rpm": info["max_rpm"],
            "rpd": info["max_rpd"],
            "context": f"{info['context_window'] // 1024}k",
            "desc": info["description"],
            "desc_en": info["description_en"],
            "category": info.get("category", "General"),
        })
    return choices
