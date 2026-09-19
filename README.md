# Gemini Code (geminicode)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/Powered%20By-Google%20Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white" alt="Google Gemini">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="MIT License">
  <img src="https://img.shields.io/badge/PRs-Welcome-brightgreen?style=for-the-badge" alt="PRs Welcome">
</p>

```text
  ____ _____ __  __ ___ _   _ ___   ____ ___  ____  _____ 
 / ___| ____|  \/  |_ _| \ | |_ _| / ___/ _ \|  _ \| ____|
| |  _|  _| | |\/| || ||  \| || | | |  | | | | | | |  _|  
| |_| | |___| |  | || || |\  || | | |__| |_| | |_| | |___ 
 \____|_____|_|  |_|___|_| \_|___| \____\___/|____/|_____|
```

> **Бесплатный терминальный ИИ-ассистент программиста с открытым исходным кодом.**  
> Вдохновлен **Claude Code**, но работает на **Google Gemini** через бесплатный API-ключ Google AI Studio. Запускается глобальной командой `geminicode` в любой папке вашего компьютера. Включает проверку доверия к рабочей области, автономных субагентов, трекер квот и безопасный вывод в Windows CMD.

[English Documentation Below](#english-overview)

---

## Главные возможности

- **Абсолютно бесплатно:** Официальный бесплатный ключ [Google AI Studio](https://aistudio.google.com/app/apikey) (15 запросов в минуту и 1,500 запросов в день на Flash-моделях с контекстом 1 000 000 токенов).
- **Глобальная команда `geminicode`:** Установите один раз и запускайте ассистента в любой рабочей директории.
- **Проверка доверия к рабочей области:** Как и в Claude Code, перед началом работы в новой папке запрашивается подтверждение безопасности.
- **Инструменты разработчика:**
  - `View`: чтение файлов с нумерацией строк.
  - `Edit`: точечное редактирование с цветным Git-style diff перед сохранением.
  - `FileCreate` и `FileDelete`: создание и удаление файлов.
  - `Bash`: выполнение консольных команд с запросом подтверждения `[y/n/always]`.
  - `Glob` и `Grep`: поиск по кодовой базе.
- **Автономные субагенты (`/subagent`):** Planner (Архитектор), Coder (Кодер), Reviewer (Ревьюер), Tester (Тестировщик).
- **Живой HUD квот:** Наглядный статус-бар с лимитами RPM и RPD.
- **Защита Windows CMD от битых символов:** 100% безопасные ASCII-рамки и символы без знаков вопроса в квадратах.
- **Умная сеть для РФ:** Автоматическое определение локальных прокси (V2Ray, Clash, Hiddify) и прямого доступа.
- **Чистый открытый код без ложных срабатываний антивируса:** Никаких закрытых бинарников — только чистые скрипты Node.js и Python.
- **Мобильный PWA на iPhone:** Веб-терминал на GitHub Pages для работы со смартфона.

---

## Быстрый старт

### Вариант 1: Установка через NPM (Рекомендуется для всех ОС)

```bash
# Устанавливаем глобально
npm install -g github:evgeniynekroz/gemini-code

# Заходим в ЛЮБУЮ папку с проектом и запускаем:
geminicode
```
*(Или мгновенный запуск без постоянной установки: `npx github:evgeniynekroz/gemini-code`)*

---

### Вариант 2: Мгновенная установка на Windows через PowerShell (1 команда)

Откройте PowerShell и вставьте одну строку:
```powershell
powershell -ExecutionPolicy Bypass -c "irm https://raw.githubusercontent.com/evgeniynekroz/gemini-code/main/install.ps1 | iex"
```
*(Скрипт сам установит зависимости и зарегистрирует команду `geminicode` в системном `PATH`)*.

---

### Вариант 3: Ручная установка через Git и Python (Windows / macOS / Linux)

```bash
# Клонируем репозиторий
git clone https://github.com/evgeniynekroz/gemini-code.git
cd gemini-code

# На Windows запускаем установщик:
powershell -ExecutionPolicy Bypass -File .\install.ps1

# Либо на macOS/Linux:
pip install -e .
```

---

### Как запускать
После любой из установок выше команда **`geminicode`** доступна **в любой папке компьютера**!  
Рабочая область Gemini Code автоматически привяжется именно к этой папке.

```bash
# Интерактивный режим (REPL)
geminicode

# Передача начального промпта (выполняет промпт и оставляет интерактивный диалог открытым)
geminicode "Объясни структуру и назначение файлов этого проекта"

# Неинтерактивный Print-режим (Claude Code -p style: выводит ответ и сразу завершает работу)
geminicode -p "Напиши функцию быстрого возведения в степень"

# Передача данных через конвейер (Piping stdin)
cat server.py | geminicode -p "Найди потенциальные уязвимости в коде"
git diff | geminicode -p "Сделай code review изменений"

# Выбор модели напрямую через CLI флаг -m / --model
geminicode -m 2.0-pro -p "Проведи архитектурный анализ этого модуля"

# Пропуск запросов подтверждения (для скриптов и автоматизации)
geminicode --dangerously-skip-permissions -p "Проанализируй тесты"

# Справка по всем флагам и версия
geminicode --help
geminicode -v
```

---

## Первый запуск

1. Выберите язык интерфейса: `[1] Русский` или `[2] English`.
2. В браузере сразу откроется страница создания ключа: [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey).
3. Скопируйте бесплатный ключ и вставьте в терминал (сохраняется мгновенно без сетевых задержек).
4. Подтвердите доверие к текущей папке проекта `[y]`.
5. Готово! Откроется чистый интерактивный интерфейс.

---

## Список команд (Claude Code Style)

| Команда | Описание |
| :--- | :--- |
| `!<команда>` | **Прямое выполнение в шелле** (например: `!git status`, `!pytest`, `!dir`) без запроса к ИИ |
| `/help` | Показать интерактивную справку по всем командам |
| `/model` | Интерактивный выбор актуальных моделей (`2.0-flash`, `2.0-pro`, `thinking`, `lite`, `1.5-pro`) |
| `/models` | Полный каталог всех моделей + обновление из Google AI Studio API (`/models refresh`) |
| `/proxy` | **Центр управления сетью и обходом блокировок для РФ** (автопоиск V2Ray/Clash, свой Cloudflare Worker, пинг) |
| `/quota`, `/cost` | Подробная таблица текущих лимитов RPM/RPD и расхода токенов |
| `/config` | Таблица текущей конфигурации (модель, язык, путь к конфигу, авто-подтверждения) |
| `/key`, `/login` | Быстро изменить или обновить API-ключ Google AI Studio |
| `/diff` | Просмотр текущего незакоммиченного `git diff` с цветной подсветкой |
| `/review` | Моментальный аудит незакоммиченных изменений в коде субагентом-ревьюером |
| `/commit` | Генерация понятного conventional commit по `git diff` и коммит в 1 клик |
| `/undo` | Откат последней правки файла |
| `/subagent <роль>` | Переключить субагента (`planner`, `coder`, `reviewer`, `tester`) |
| `/doctor` | Полная диагностика системы: пинг до Gemini, статус обхода гео-блокировки, Git, Python |
| `/init` | Умный анализ проекта и создание файла `GEMINI.md` с инструкциями и правилами |
| `/compact` | Сжатие истории диалога для экономии контекста |
| `/clear` или `/cls` | Очистка контекста диалога и экрана |
| `/exit` | Выход из программы |

---

## Актуальные модели Google AI Studio

- **`gemini-2.0-flash`** *(По умолчанию)*: Флагманская модель нового поколения с непревзойденной скоростью, контекстом 1 000 000 токенов и лимитом 15 RPM / 1500 RPD (Free Tier).
- **`gemini-2.0-flash-lite`**: Сверхбыстрая и экономичная модель с минимальной задержкой и повышенным лимитом 30 RPM.
- **`gemini-2.0-pro-exp-02-05`**: Лучшая модель Google для сложного кодинга, проектирования архитектуры и глубокого рефакторинга.
- **`gemini-2.0-flash-thinking-exp-01-21`**: Модель с глубоким пошаговым рассуждением (Chain-of-Thought) и отдельным отображением мыслей ассистента.
- **`gemini-1.5-pro`**: Мощная классическая Pro-модель с контекстом 2 000 000 токенов.
- **`gemini-1.5-flash`**: Проверенная рабочая лошадка для быстрого написания кода.
- **`gemini-1.5-flash-8b`**: Сверхлегкая модель для простых повторяющихся задач.

---

## Работа из России (Обход ограничений)

Gemini Code имеет встроенную систему адаптивного сетевого роутинга:
1. **Автоопределение локального VPN/прокси:** При запуске или через команду `/proxy -> 1` автоматически сканируются и тестируются порты популярных клиентов (V2RayN, Xray, Clash, Mihomo, Hiddify, Shadowsocks).
2. **Бесплатный Cloudflare Worker (Custom Base URL):** Команда `/proxy -> 6` предоставляет готовый 5-строчный JS-скрипт, который разворачивается бесплатно за 1 минуту на `workers.cloudflare.com` и навсегда открывает доступ из РФ с лимитом 100 000 запросов в сутки без необходимости включать VPN.
3. **Прямой ввод адреса прокси:** Поддержка `http://` и `socks5://` прокси с авторизацией или без.


---

## Запуск на iPhone

1. **Через GitHub Pages (Web-терминал PWA):**
   - Откройте страницу репозитория на телефоне в Safari.
   - Нажмите кнопку *«Поделиться»* -> *«На экран „Домой“»*.
   - Открывайте как нативное приложение, укажите ключ в настройках и работайте с кодом.
2. **Через приложение a-Shell:**
   - Установите бесплатное приложение **a-Shell** из App Store.
   - Выполните: `pip install geminicode && geminicode`.

---

## Поддержать проект (Donations)

Если **Gemini Code** помогает вам в работе и экономит деньги на платных подписках — поддержите автора!  
🎯 **Текущий сбор:** **На нормальный рабочий ноутбук** (Цель: 35 000 ₽)

- 🎁 **DonationAlerts:** **[donationalerts.com/r/nekrozdev](https://www.donationalerts.com/r/nekrozdev)**
- 💎 **CryptoBot (USDT / TON / BTC / Любая сумма):** **[t.me/send?start=IVj4UTox7JMD](https://t.me/send?start=IVj4UTox7JMD)**

---

## English Overview

**Gemini Code** (`geminicode`) is an open-source, completely free autonomous terminal coding assistant inspired by **Claude Code**, powered by **Google Gemini** via the Google AI Studio free tier.

### Highlights:
- **Global `geminicode` CLI:** Run in any directory on your computer.
- **Workspace Trust Confirmation:** Confirm directory access before granting file operations.
- **Instant Onboarding:** Fast key setup without network verification loops.
- **Safe ASCII Windows CMD Support:** Zero broken characters or question-mark glyphs.
- **Claude Code Style Tools:** File viewer, diff-based editor, command executor with confirmation, and autonomous subagents.

```bash
# Global install via npm:
npm install -g github:evgeniynekroz/gemini-code

# Open any project folder and run interactive session:
geminicode

# Pass initial prompt directly:
geminicode "Explain this project structure"

# Non-interactive print mode (Claude Code -p style):
geminicode -p "Write a python unit test"

# Pipe code or logs directly into geminicode:
cat server.py | geminicode -p "Find security issues"
git diff | geminicode -p "Generate commit message"

# Show help & version:
geminicode --help
geminicode -v
```

---

## Лицензия

Проект распространяется под открытой лицензией [MIT](LICENSE).  
Автор: **evgeniynekroz**
