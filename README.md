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

### Вариант 2: Установка через Git и Python (Windows / macOS / Linux)

```bash
# 1. Клонируем репозиторий
git clone https://github.com/evgeniynekroz/gemini-code.git
cd gemini-code

# 2. На Windows запускаем установщик (зарегистрирует команду geminicode):
powershell -ExecutionPolicy Bypass -File .\install.ps1

# Либо на macOS/Linux:
pip install -e .
```

После установки просто откройте командную строку в любой нужной папке и напишите:
```bash
geminicode
```

---

## Первый запуск

1. Выберите язык интерфейса: `[1] Русский` или `[2] English`.
2. В браузере сразу откроется страница создания ключа: [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey).
3. Скопируйте бесплатный ключ и вставьте в терминал (сохраняется мгновенно без сетевых задержек).
4. Подтвердите доверие к текущей папке проекта `[y]`.
5. Готово! Откроется чистый интерактивный интерфейс.

---

## Список команд

| Команда | Описание |
| :--- | :--- |
| `/help` | Показать интерактивную справку по всем командам |
| `/subagent <роль>` | Переключить субагента (`planner`, `coder`, `reviewer`, `tester`) |
| `/model` | Переключатель модели (`2.5-flash`, `2.5-pro`, `thinking`) |
| `/quota` | Подробная таблица текущих лимитов и суточного расхода квоты |
| `/key` | Быстро изменить API-ключ Google AI Studio |
| `/doctor` | Диагностика системы: пинг до Gemini, статус прокси, Git, Python |
| `/init` | Создание файла `GEMINI.md` с инструкциями и правилами проекта |
| `/review` | Моментальный аудит незакоммиченных изменений в коде |
| `/commit` | Генерация понятного коммита по `git diff` и коммит в 1 клик |
| `/undo` | Откат последней правки файла |
| `/compact` | Сжатие истории диалога для экономии контекста |
| `/theme` | Переключение стиля символов (Safe ASCII / Unicode) |
| `/lang` | Переключение языка интерфейса (RU / EN) |
| `/clear` или `/cls` | Полная очистка экрана консоли и контекста |
| `/exit` | Выход из программы |

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

# Open any project folder and run:
geminicode
```

---

## Лицензия

Проект распространяется под открытой лицензией [MIT](LICENSE).  
Автор: **evgeniynekroz**
