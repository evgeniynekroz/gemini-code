"""
Gemini model definitions, context window specifications, and Free Tier rate limits.
"""

from typing import Dict, Any, List

AVAILABLE_MODELS: Dict[str, Dict[str, Any]] = {
    "gemini-2.5-flash": {
        "name": "Gemini 2.5 Flash",
        "description": "Быстрая, универсальная и высокоточная модель. Рекомендуется по умолчанию.",
        "description_en": "Fast, versatile, and high-accuracy model. Recommended default.",
        "max_rpm": 15,
        "max_rpd": 1500,
        "max_tpm": 1_000_000,
        "context_window": 1_048_576,
        "is_default": True,
    },
    "gemini-2.5-pro": {
        "name": "Gemini 2.5 Pro",
        "description": "Максимальный интеллект для сложной архитектуры и глубокого рефакторинга.",
        "description_en": "Maximum reasoning power for complex architecture and deep refactoring.",
        "max_rpm": 2,
        "max_rpd": 50,
        "max_tpm": 32_000,
        "context_window": 2_097_152,
        "is_default": False,
    },
    "gemini-2.0-flash": {
        "name": "Gemini 2.0 Flash",
        "description": "Молниеносная скорость генерации, оптимизирована для быстрого кодинга.",
        "description_en": "Blazing fast generation speed, optimized for quick iterations.",
        "max_rpm": 15,
        "max_rpd": 1500,
        "max_tpm": 1_000_000,
        "context_window": 1_048_576,
        "is_default": False,
    },
    "gemini-2.0-flash-thinking-exp": {
        "name": "Gemini 2.0 Flash Thinking",
        "description": "Экспериментальная модель с пошаговым рассуждением (CoT) перед ответом.",
        "description_en": "Experimental model with step-by-step reasoning (CoT) before output.",
        "max_rpm": 10,
        "max_rpd": 1500,
        "max_tpm": 1_000_000,
        "context_window": 1_048_576,
        "is_default": False,
    },
    "gemini-1.5-flash": {
        "name": "Gemini 1.5 Flash",
        "description": "Стабильная базовая модель с окном в 1 млн токенов.",
        "description_en": "Stable base model with 1M token context window.",
        "max_rpm": 15,
        "max_rpd": 1500,
        "max_tpm": 1_000_000,
        "context_window": 1_048_576,
        "is_default": False,
    },
    "gemini-1.5-pro": {
        "name": "Gemini 1.5 Pro",
        "description": "Классическая Pro-модель с гигантским контекстом в 2 млн токенов.",
        "description_en": "Classic Pro model with massive 2M token context window.",
        "max_rpm": 2,
        "max_rpd": 50,
        "max_tpm": 32_000,
        "context_window": 2_097_152,
        "is_default": False,
    },
}

def get_model_info(model_id: str) -> Dict[str, Any]:
    # Strip optional 'models/' prefix
    clean_id = model_id.replace("models/", "")
    return AVAILABLE_MODELS.get(clean_id, AVAILABLE_MODELS["gemini-2.5-flash"])

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
        })
    return choices
