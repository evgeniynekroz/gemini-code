"""
Internationalization (i18n) module with Russian and English translations.
"""

MESSAGES = {
    "ru": {
        # App & Banner
        "app_title": "Gemini Code",
        "app_subtitle": "Терминальный ИИ-ассистент программиста на базе Google Gemini",
        "welcome": "Добро пожаловать в Gemini Code! Создан для быстрой и удобной разработки.",
        "lang_selected": "Выбран язык: Русский",
        
        # Onboarding
        "onboarding_title": "Первоначальная настройка Gemini Code",
        "choose_lang": "Выберите язык интерфейса / Select language:",
        "api_key_prompt": "Введите ваш API-ключ Google AI Studio (получить бесплатно: https://aistudio.google.com/app/apikey): ",
        "api_key_saved": "API-ключ успешно сохранен!",
        "api_key_invalid": "Неверный API-ключ. Проверьте правильность и попробуйте снова.",
        
        # Connectivity & Proxy
        "checking_connection": "Проверка сетевого подключения к Google Gemini...",
        "conn_direct_ok": "Прямое подключение активно! Обход блокировок не требуется.",
        "conn_blocked": "Прямой доступ к Google Gemini заблокирован в вашем регионе.",
        "scanning_local_proxy": "Поиск локальных прокси (V2Ray / Xray / Clash / Hiddify)...",
        "local_proxy_found": "Обнаружен локальный прокси на {proxy}! Автоматическое подключение.",
        "trying_smartdns": "Подключение через SmartDNS / Luna DNS...",
        "smartdns_ok": "SmartDNS успешно активирован (доступ разблокирован).",
        "trying_mirror": "Подключение через резервное зеркало...",
        "conn_all_failed": "Не удалось установить соединение с серверами Gemini. Проверьте VPN или настройте /proxy.",
        
        # Quota HUD
        "quota_hud": "[{model} | RPM: {rpm}/{max_rpm} | Запросы сегодня: {rpd}/{max_rpd}]",
        "quota_rpm_warning": "Внимание: приближение к минутному лимиту запросов ({rpm}/{max_rpm})!",
        "quota_rpd_warning": "Внимание: приближение к суточному лимиту ({rpd}/{max_rpd})!",
        
        # Tools & Approvals
        "confirm_command": "Выполнить команду в терминале: `{cmd}`?\n[y] Да | [n] Нет | [a] Разрешать всегда в этой сессии: ",
        "command_rejected": "Команда отклонена пользователем.",
        "confirm_edit": "Применить изменения к файлу `{path}`?",
        "edit_rejected": "Редактирование отклонено пользователем.",
        "file_created": "Создан файл: {path}",
        "file_deleted": "Удален файл: {path}",
        "file_edited": "Изменен файл: {path}",
        
        # Commands
        "cmd_help": "Показать справку по всем командам",
        "cmd_model": "Сменить активную модель (Flash, Pro, Thinking)",
        "cmd_quota": "Показать текущую статистику использования квот",
        "cmd_proxy": "Управление сетевым режимом и прокси",
        "cmd_doctor": "Запустить полную диагностику системы и сети",
        "cmd_init": "Создать файл GEMINI.md с правилами для проекта",
        "cmd_subagent": "Переключить субагента (planner, coder, reviewer, tester)",
        "cmd_review": "Провести быстрый аудит незакоммиченных изменений в Git",
        "cmd_commit": "Автоматически сгенерировать коммит по git diff",
        "cmd_undo": "Откатить последнее изменение файла",
        "cmd_compact": "Сжать историю диалога для экономии токенов",
        "cmd_theme": "Переключить стиль символов (Safe для CMD / Modern Unicode)",
        "cmd_lang": "Сменить язык (RU / EN)",
        "cmd_clear": "Очистить текущий контекст диалога",
        "cmd_exit": "Выйти из программы",
        
        # Subagents
        "subagent_active": "Активен субагент: [{role}]",
        "subagent_planner_desc": "Архитектор: исследует кодовую базу и составляет детальный план без правок кода.",
        "subagent_coder_desc": "Кодер: пишет чистый, протестированный код и применяет правки через diff.",
        "subagent_reviewer_desc": "Ревьюер: проверяет код на уязвимости, баги и соответствие лучшим практикам.",
        "subagent_tester_desc": "Тестировщик: создает и запускает юнит-тесты.",
        
        # Miscellaneous
        "prompt_placeholder": "Введите задачу или команду (/help)...",
        "thinking": "Рассуждение...",
        "context_cleared": "Контекст диалога очищен.",
        "goodbye": "До встречи! Удачного кодинга!",
    },
    
    "en": {
        # App & Banner
        "app_title": "Gemini Code",
        "app_subtitle": "Terminal AI Coding Assistant powered by Google Gemini",
        "welcome": "Welcome to Gemini Code! Built for fast and intuitive terminal coding.",
        "lang_selected": "Selected language: English",
        
        # Onboarding
        "onboarding_title": "Initial Setup for Gemini Code",
        "choose_lang": "Select interface language / Выберите язык:",
        "api_key_prompt": "Enter your Google AI Studio API Key (get for free at https://aistudio.google.com/app/apikey): ",
        "api_key_saved": "API key successfully saved!",
        "api_key_invalid": "Invalid API key. Please check and try again.",
        
        # Connectivity & Proxy
        "checking_connection": "Checking network connectivity to Google Gemini...",
        "conn_direct_ok": "Direct connection is active! No proxy needed.",
        "conn_blocked": "Direct connection to Google Gemini is restricted in your region.",
        "scanning_local_proxy": "Scanning for local proxies (V2Ray / Xray / Clash / Hiddify)...",
        "local_proxy_found": "Found active local proxy at {proxy}! Connected automatically.",
        "trying_smartdns": "Connecting via SmartDNS / Luna DNS...",
        "smartdns_ok": "SmartDNS activated successfully (access unblocked).",
        "trying_mirror": "Connecting via backup reverse mirror...",
        "conn_all_failed": "Could not connect to Gemini servers. Please check your VPN or configure /proxy.",
        
        # Quota HUD
        "quota_hud": "[{model} | RPM: {rpm}/{max_rpm} | Daily Requests: {rpd}/{max_rpd}]",
        "quota_rpm_warning": "Warning: Approaching per-minute request limit ({rpm}/{max_rpm})!",
        "quota_rpd_warning": "Warning: Approaching daily request limit ({rpd}/{max_rpd})!",
        
        # Tools & Approvals
        "confirm_command": "Run terminal command: `{cmd}`?\n[y] Yes | [n] No | [a] Always allow this session: ",
        "command_rejected": "Command execution rejected by user.",
        "confirm_edit": "Apply modifications to file `{path}`?",
        "edit_rejected": "File editing rejected by user.",
        "file_created": "File created: {path}",
        "file_deleted": "File deleted: {path}",
        "file_edited": "File modified: {path}",
        
        # Commands
        "cmd_help": "Show help and available commands",
        "cmd_model": "Switch active model (Flash, Pro, Thinking)",
        "cmd_quota": "Show active quota and limit usage",
        "cmd_proxy": "Manage network mode and proxy settings",
        "cmd_doctor": "Run full environment and connectivity diagnostic",
        "cmd_init": "Generate GEMINI.md instructions for this repository",
        "cmd_subagent": "Switch specialized subagent (planner, coder, reviewer, tester)",
        "cmd_review": "Instant code review for uncommitted git changes",
        "cmd_commit": "Auto-generate conventional git commit from diff",
        "cmd_undo": "Revert the last file modification",
        "cmd_compact": "Compact conversation history to conserve tokens",
        "cmd_theme": "Toggle symbol theme (Safe for CMD / Modern Unicode)",
        "cmd_lang": "Change interface language (RU / EN)",
        "cmd_clear": "Clear current conversation context",
        "cmd_exit": "Exit application",
        
        # Subagents
        "subagent_active": "Active subagent: [{role}]",
        "subagent_planner_desc": "Architect: analyzes project and plans step-by-step tasks without modifying code.",
        "subagent_coder_desc": "Coder: writes clean, tested code and executes diff patches.",
        "subagent_reviewer_desc": "Reviewer: inspects code for vulnerabilities, bugs, and best practices.",
        "subagent_tester_desc": "Tester: writes and runs automated unit tests.",
        
        # Miscellaneous
        "prompt_placeholder": "Type a task or command (/help)...",
        "thinking": "Thinking...",
        "context_cleared": "Conversation context cleared.",
        "goodbye": "Goodbye! Happy coding!",
    }
}

class I18n:
    def __init__(self, lang: str = "ru"):
        self.lang = lang if lang in MESSAGES else "ru"

    def set_lang(self, lang: str):
        if lang in MESSAGES:
            self.lang = lang

    def t(self, key: str, **kwargs) -> str:
        text = MESSAGES.get(self.lang, {}).get(key, MESSAGES["ru"].get(key, key))
        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text

# Global singleton
i18n = I18n()
