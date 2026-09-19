# ⚡ Gemini Code

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
> Вдохновлен **Claude Code**, но работает на **Google Gemini** через бесплатный API-ключ Google AI Studio. Включает автономных субагентов, живой трекер квот, защиту от битых символов в Windows CMD и автоматический обход блокировок в РФ.

[English Documentation Below](#-english-overview)

---

## 🌟 Главные фичи

- 💸 **Абсолютно бесплатно:** Работает через официальный бесплатный ключ [Google AI Studio](https://aistudio.google.com/app/apikey) (15 запросов в минуту и 1,500 запросов в день на моделях Flash с окном в 1 миллион токенов!).
- 🤖 **Функционал уровня Claude Code:**
  - `View`: чтение файлов с номерами строк.
  - `Edit`: точечная правка файлов с цветным **Git-style Diff** (зеленый `+`, красный `-`) перед сохранением.
  - `FileCreate` и `FileDelete`: безопасное создание и удаление файлов.
  - `Bash`: запуск терминальных команд (PowerShell / Bash) с запросом подтверждения `[y/n/a]`.
  - `Glob` и `Grep`: мгновенный поиск файлов и строк по всему проекту.
- 👥 **Автономные субагенты (`/subagent`):**
  - **Planner / Architect:** исследует проект и составляет детальный пошаговый план без правок кода.
  - **Coder:** специализированный агент для написания и рефакторинга кода.
  - **Reviewer:** аудит кода на баги, уязвимости (OWASP) и стиль.
  - **Tester:** автоматическое написание и прогон юнит-тестов.
- 📊 **Живой HUD квот и лимитов:** Прямо в терминале отображает, сколько запросов в минуту (RPM) и день (RPD) израсходовано и сколько осталось до сброса.
- 🌐 **Умная сеть и обход блокировок для РФ:**
  1. *Прямой пинг:* если у вас уже есть VPN — работает напрямую без задержек.
  2. *Автопоиск локального VPN:* проверяет порты `10808`, `10809`, `7890`, `2080` (V2Ray, Xray, Clash, Hiddify) и подключается сам.
  3. *SmartDNS (Luna DNS / Comss DNS):* встроенный резолвер для обхода цензуры на уровне приложения.
  4. *Резервные зеркала:* пул публичных реверс-прокси серверов.
- 🪟 **Защита от знаков вопроса в квадратах [?] в Windows CMD:**
  - Автоматический перевод консоли в UTF-8 (`chcp 65001`).
  - Специальный безопасный режим (`/theme safe`): аккуратные текстовые плашки `[OK]`, `[FAIL]`, `[GEMINI]`, `-->` и рамки `┌─┐│└─┘`, которые никогда не ломаются в стандартном CMD.
- 📱 **Поддержка iPhone (100% бесплатно, без своего сервера):**
  - Мобильный Web-терминал PWA на **GitHub Pages** (добавляется на домашний экран iOS).
  - Поддержка запуска в бесплатном iOS-терминале **a-Shell**.
- 🚀 **Облачная сборка бинарников (GitHub Actions):**
  - Готовые `.exe` (64-бит и 32-бит для Windows), бинарники для macOS и Linux компилируются в облаке GitHub и доступны во вкладке Releases.

---

## 🚀 Быстрый старт

### 1. Установка через Git и Pip

```bash
# Клонируем репозиторий
git clone https://github.com/evgeniynekroz/gemini-code.git
cd gemini-code

# Устанавливаем зависимости
pip install -e .

# Запускаем!
gemini-code
```

### 2. Первый запуск (Онбординг)
1. Выберите язык: `[1] Русский` или `[2] English`.
2. Программа проверит подключение к серверам Google Gemini.
3. Получите бесплатный ключ на [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) и вставьте в консоль.
4. Готово! Появится статус-бар и приглашение к работе.

---

## ⌨️ Список команд

| Команда | Описание |
| :--- | :--- |
| `/help` | Показать интерактивную справку по всем командам |
| `/subagent <роль>` | Переключить субагента (`planner`, `coder`, `reviewer`, `tester`) |
| `/model` | Интерактивный переключатель модели (`2.5-flash`, `2.5-pro`, `thinking`) |
| `/quota` | Подробная таблица текущих лимитов и суточного расхода квоты |
| `/doctor` | Диагностика системы: пинг до Gemini, статус прокси, Git, Python |
| `/init` | Создание файла `GEMINI.md` с инструкциями и правилами проекта |
| `/review` | Моментальный аудит незакоммиченных изменений в коде |
| `/commit` | Генерация понятного коммита по `git diff` и коммит в 1 клик |
| `/undo` | Откат последней правки файла |
| `/compact` | Сжатие истории диалога для экономии контекста |
| `/theme` | Переключение между Modern Unicode и Safe-ASCII для Windows CMD |
| `/lang` | Переключение языка интерфейса (RU / EN) |
| `/clear` | Очистка истории диалога |
| `/exit` | Выход из программы |

---

## 📱 Запуск на iPhone

1. **Через GitHub Pages (Web-терминал PWA):**
   - Откройте страницу репозитория на телефоне.
   - В Safari нажмите кнопку *«Поделиться»* -> *«На экран „Домой“»*.
   - Открывайте как обычное приложение, введите ключ в настройках (⚙) и пишите код на ходу!
2. **Через приложение a-Shell:**
   - Установите бесплатное приложение **a-Shell** из App Store.
   - Выполните: `pip install gemini-code-cli && gemini-code`.

---

## ☕ Поддержать проект (Donations)

Если Gemini Code помогает вам экономить время и деньги на подписках — поддержите автора! Все донаты идут на развитие утилиты и поддержание серверов-зеркал.

- **Boosty:** [boosty.to/evgeniynekroz](https://boosty.to) *(добавьте вашу ссылку)*
- **ЮMoney:** [yoomoney.ru/to/...](https://yoomoney.ru) *(добавьте ваш номер кошелька)*
- **USDT (TRC20):** `Txxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
- **TON:** `EQxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
- **Bitcoin:** `bc1qxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

---

## 🌍 English Overview

**Gemini Code** is an open-source, completely free autonomous terminal coding assistant inspired by **Claude Code**, powered by **Google Gemini** via the Google AI Studio free tier.

### Key Highlights:
- **Free Quota:** 15 RPM / 1,500 RPD on Flash models with a 1M token context window.
- **Claude Code Tools:** `view_file`, diff-based `edit_file`, `create_file`, safe `run_command` with confirmations, `glob_files`, `grep_search`, and git operations.
- **Specialized Subagents:** Planner, Coder, Reviewer, and Tester.
- **Live Quota HUD:** Visual indicator of per-minute and per-day usage.
- **Windows CMD Safe Mode:** Zero broken unicode characters in classic terminals.
- **Mobile iPhone PWA:** 100% client-side web terminal deployed to GitHub Pages.
- **Automated Cloud Releases:** GitHub Actions workflow builds standalone executables for Windows x64/x86, macOS, and Linux.

### Quick Start (EN):
```bash
git clone https://github.com/evgeniynekroz/gemini-code.git
cd gemini-code
pip install -e .
gemini-code
```

---

## 📄 Лицензия

Проект распространяется под открытой лицензией [MIT](LICENSE).
Автор: **evgeniynekroz**
