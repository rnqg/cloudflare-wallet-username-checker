# Чекер юзернеймов Cloudflare Wallet

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![CI](https://github.com/rnqg/cloudflare-wallet-username-checker/actions/workflows/ci.yml/badge.svg)](https://github.com/rnqg/cloudflare-wallet-username-checker/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-26A5E4?logo=telegram&logoColor=white)](#telegram-бот)

[English](README.md) · **Русский**

Асинхронный CLI, возобновляемый перебор трёхсимвольных имён и двуязычный Telegram-бот для
проверки юзернеймов кошелька `cloudflare.pay`.

> Это неофициальный проект сообщества. Он не связан с Cloudflare и не одобрен компанией.

## Зачем нужен отдельный чекер

Поведение видимой страницы не позволяет точно определить доступность. И свободные, и некоторые
зарезервированные Cloudflare имена могут перенаправляться на форму резервирования. Проект использует
публичный endpoint доступности и разделяет ответы:

| Состояние API | Значение | Файл |
| --- | --- | --- |
| `available: true` | Сейчас можно зарезервировать | `available.txt` |
| `TAG_TAKEN` | Уже занято | `taken.txt` |
| `RESERVED_TAG` | Зарезервировано Cloudflare | `reserved.txt` |
| `INVALID_TAG` | Некорректное имя | `invalid.txt` |
| Ошибка сети/API | Результат неизвестен | `error.txt` |

Неизвестный ответ никогда не помечается как свободный.

## Возможности

- HTTP/2 и повторное использование соединений с ограниченной параллельностью
- повторы с экспоненциальной задержкой и поддержкой `Retry-After`
- проверка одного имени, списка или файла
- JSON-вывод и отдельный файл для каждого статуса
- возобновляемый перебор всех трёхсимвольных комбинаций
- Telegram-бот на русском и английском с сохранением выбранного языка
- Telegram premium custom emoji и форматированные сообщения
- Docker и Docker Compose
- CI для Python 3.10–3.13, тесты, Ruff и строгий mypy

## Быстрый запуск

```bash
git clone https://github.com/rnqg/cloudflare-wallet-username-checker.git
cd cloudflare-wallet-username-checker
python -m venv .venv
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Установка:

```bash
python -m pip install --upgrade pip
python -m pip install -e .
```

Проверить несколько имён:

```bash
cfwallet qqq x402agent my-wallet --lang ru
```

Проверить файл:

```bash
cfwallet --input examples/usernames.txt --workers 5 --lang ru
```

Получить JSON:

```bash
cfwallet qqq x402agent --json
```

По умолчанию результаты сохраняются в `output/`. Путь меняется через `--output-dir`.

## Полный перебор трёхсимвольных имён

После каждого ответа сканер дописывает JSONL-checkpoint. Повторный запуск той же команды продолжает
проверку и повторяет только пропущенные или ошибочные запросы.

Буквы и цифры, 36³ комбинаций:

```bash
cfwallet-exhaustive --alphabet alnum --workers 20
```

Буквы, цифры и дефис, 37³ комбинаций:

```bash
cfwallet-exhaustive --alphabet all --workers 20
```

Не завышайте число потоков. Большая параллельность может усилить rate-limit и замедлить проверку.
Не запускайте повторные полные сканирования без нормальной причины.

## Telegram-бот

Бот работает на русском и английском, поддерживает `/check`, списки имён обычным текстом, переключение
языка и раздельные статусы. В SQLite сохраняется только выбранный пользователем язык. Проверяемые имена
не сохраняются.

Создайте бота через [@BotFather](https://t.me/BotFather), затем подготовьте окружение:

```bash
cp .env.example .env
```

Укажите `TELEGRAM_BOT_TOKEN` в `.env` и запустите:

```bash
set -a
source .env
set +a
cfwallet-bot
```

Windows PowerShell:

```powershell
$env:TELEGRAM_BOT_TOKEN="1234567890:ваш_токен"
cfwallet-bot
```

Команды:

| Команда | Назначение |
| --- | --- |
| `/start` | Открыть чекер |
| `/check name1 name2` | Проверить имена |
| `/language` | Переключить RU/EN |
| `/help` | Показать помощь |
| `/about` | Информация о проекте |

### Docker Compose

```bash
cp .env.example .env
docker compose up -d --build
docker compose logs -f bot
```

SQLite-база сохраняется в `./data`.

## Параметры CLI

```text
cfwallet [-i ФАЙЛ] [-o ПАПКА] [--workers N] [--timeout СЕКУНДЫ]
         [--retries N] [--lang en|ru] [--json] [--quiet] [ИМЯ ...]
```

Допустимый формат: 3–32 латинские буквы, цифры или дефисы. Нормализация и окончательная проверка
выполняются API.

## Ответственное использование

- Доступность меняется; резервируйте имя только через официальный сайт.
- Проект не автоматизирует резервирование и не обходит авторизацию.
- Соблюдайте ограничения и условия Cloudflare.
- Не используйте инструмент для нарушения работы сервиса, сбора данных или злоупотребления товарными знаками.
- Не добавляйте в Git `.env`, токены, базы, checkpoint и выгрузки результатов.

## Разработка

```bash
python -m pip install -e ".[dev]"
ruff check .
ruff format --check .
pytest
mypy
```

Дополнительно: [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md) и
[описание архитектуры](docs/ARCHITECTURE.md).

## Лицензия

[MIT](LICENSE)
