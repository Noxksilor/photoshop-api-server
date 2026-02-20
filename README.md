# Photoshop API Server

Минимальный HTTP-сервер для работы с Adobe Photoshop через API с использованием JSX-скриптов.

## Quick Start (для ленивых)

Сделайте всё в 5 шагов, чтобы проверить, что всё работает:

1. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

2. Создайте config.json:
   ```bash
   copy config.example.json config.json
   ```

3. Положите тестовый файл в `C:\ps_jobs\input\source.png` (нарисуйте или найдите любую PNG-картинку).

4. Запустите сервер в одном окне:
   ```bash
   python server.py
   ```

5. Запустите тест-клиент в другом окне:
   ```bash
   python test_client.py
   ```

Ожидаемый результат: Photoshop запускается, а в `C:\ps_jobs\api_tests\test_result.png` появляется обработанный PNG.

## Запуск одним файлом (для ленивых)

Если не хочется возиться с двумя окнами и командами:

1. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

2. Создайте config.json:
   ```bash
   copy config.example.json config.json
   ```

3. Положите PNG в путь `default_input` из config.json (по умолчанию `C:\ps_jobs\input\source.png`).

4. В проводнике дважды кликните `run_all.bat`.

Ожидание:
- Если всё ок — файл `C:\ps_jobs\api_tests\test_result.png`
- Иначе — в окне консоли понятное `ERROR: ...`.

## Watcher (минимум действий для пользователя)

Для автоматического запуска тестов и сбора отчётов:

1. Обновите репозиторий:
   ```bash
   git pull
   ```

2. Убедитесь, что `config.json` и `C:\ps_jobs\input\source.png` настроены.

3. Запустите watcher:
   ```bash
   python watcher.py
   ```

Watcher будет:
- Запускать `run_all.ps1` повторно
- Сохранять отчёты в папку `logs/run-YYYYMMDD-HHMMSS/`
- Остановиться после 3 последовательных успешных запусков
- Дожидаться 60 секунд между запусками

4. После завершения работы сохраните логи:
   ```bash
   git add logs/*
   git commit -m "watcher runs"
   git push
   ```

Теперь можно запустить сессию Kilo для анализа и правки кода.

## Установка

1. Клонируйте репозиторий
2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
3. Создайте файл `config.json` из примера:
   ```bash
   copy config.example.json config.json
   ```
4. Отредактируйте `config.json` под вашу систему (проверьте пути к Photoshop и рабочим папкам)

## Запуск сервера

```bash
uvicorn server:app --host 0.0.0.0 --port 8000
```

Сервер будет доступен по адресу `http://localhost:8000`

## API Эндпоинты

### POST /run_script

Выполняет JSX-скрипт в Adobe Photoshop и возвращает результат в виде PNG-изображения.

**Тело запроса (JSON):**
```json
{
  "script_text": "<jsx-код>",
  "output_name": "result.png"
}
```

**Параметры:**
- `script_text` (обязательно): Строка с JSX-скриптом для Photoshop
- `output_name` (необязательно): Имя выходного файла (по умолчанию `result.png`)

**Пример запроса с помощью curl:**
```bash
curl -X POST "http://localhost:8000/run_script" ^
  -H "Content-Type: application/json" ^
  -d "{\"script_text\": \"$(type example_script.jsx)\", \"output_name\": \"inverted.png\"}" ^
  -o inverted_result.png
```

## Примеры скриптов

В репозитории есть пример скрипта `example_script.jsx`, который:
1. Открывает файл `default_input` из конфига
2. Инвертирует цвета изображения
3. Сохраняет результат как PNG в папку задачи

### Плейсхолдеры в скриптах

Скрипты могут использовать следующие плейсхолдеры, которые будут заменены сервером перед запуском:
- `{{INPUT_PATH}}`: Путь к входному файлу (из `default_input` в конфиге)
- `{{OUTPUT_PATH}}`: Путь к выходному файлу (создается автоматически)

## Конфигурация

Пример конфигурационного файла `config.json`:
```json
{
  "photoshop_path": "C:\\Program Files\\Adobe\\Adobe Photoshop\\Photoshop.exe",
  "work_dir": "C:\\ps_jobs\\api_jobs",
  "default_input": "C:\\ps_jobs\\input\\source.png",
  "default_output_name": "result.png",
  "max_execution_seconds": 300
}
```

**Параметры:**
- `photoshop_path`: Полный путь к исполняемому файлу Photoshop
- `work_dir`: Папка для временных файлов задач
- `default_input`: Путь к стандартному входному файлу (используется в примерах)
- `default_output_name`: Стандартное имя выходного файла
- `max_execution_seconds`: Максимальное время выполнения скрипта (в секундах)

## Описание работы

1. При получении запроса сервер генерирует уникальный идентификатор задачи (UUID)
2. Создает папку для задачи в `work_dir`
3. Сохраняет JSX-скрипт в эту папку с заменой плейсхолдеров
4. Запускает Photoshop с указанным скриптом
5. Ждет завершения выполнения или таймаута
6. Проверяет наличие выходного файла
7. Возвращает результат в виде файла или ошибку

## Технологии

- **Backend:** Python 3.11+
- **Web-фреймворк:** FastAPI
- **Сервер:** Uvicorn
