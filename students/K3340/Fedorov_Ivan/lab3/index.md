# Лабораторная работа 3

## Docker, источники данных и очереди

## Цель работы

Упаковать приложение и парсер в Docker, подключить PostgreSQL, реализовать вызов парсера через HTTP и организовать фоновое выполнение задач с помощью Redis и Celery.

## Постановка задачи

В работе требовалось:

- запустить FastAPI-приложение в Docker;
- подключить базу данных PostgreSQL;
- создать сервис для парсинга веб-страниц;
- реализовать вызов парсера через HTTP;
- добавить Redis как брокер сообщений;
- добавить Celery worker для фоновых задач;
- создать endpoint для постановки парсинга в очередь;
- возвращать клиенту идентификатор задачи и её статус.

## Архитектура проекта

Проект состоит из пяти Docker-сервисов:

| Сервис | Назначение |
| --- | --- |
| `api` | API-шлюз для запросов клиента |
| `parser` | загрузка HTML и извлечение заголовка страницы |
| `worker` | выполнение задач Celery в фоне |
| `redis` | очередь задач и хранилище результатов Celery |
| `db` | PostgreSQL для хранения результатов |

## Схема работы

### Прямой вызов

```text
Клиент → API → Parser → PostgreSQL
```

Клиент отправляет URL в API. API вызывает сервис `parser` по HTTP. Parser загружает страницу, извлекает тег `<title>` и сохраняет результат в PostgreSQL.

### Вызов через очередь

```text
Клиент → API → Redis → Celery worker → PostgreSQL
```

Клиент отправляет URL. API добавляет задачу в Redis и сразу возвращает `task_id`. Worker забирает задачу, выполняет парсинг и сохраняет результат в базу.

## База данных

PostgreSQL запускается в контейнере `db`.

Параметры подключения с компьютера:

```text
Host: localhost
Port: 5433
Database: finance_db
User: postgres
Password: postgres
```

Внутри Docker-сети приложения подключаются к базе по адресу:

```text
postgresql://postgres:postgres@db:5432/finance_db
```

Результаты сохраняются в таблицу `parsed_pages`:

| Поле | Назначение |
| --- | --- |
| `id` | идентификатор записи |
| `url` | адрес страницы |
| `title` | заголовок страницы |
| `status_code` | HTTP-статус |
| `source` | способ запуска: `http` или `celery` |
| `parsed_at` | время парсинга |
| `error` | текст ошибки |

## Последовательная проверка

### Шаг 1. Запуск Docker Compose

Перейти в папку лабораторной:

```powershell
cd students/K3340/Fedorov_Ivan/lab3
docker compose up --build
```

Что проверить:

- образы собираются без ошибок;
- PostgreSQL сообщает о готовности;
- API, parser и worker запускаются.

### Шаг 2. Состояние контейнеров

В новом терминале выполнить:

```powershell
docker compose ps
```

Что проверить:

- `db` работает;
- `redis` работает;
- `parser` работает;
- `api` работает;
- `worker` работает.

### Шаг 3. Swagger API

Открыть:

```text
http://127.0.0.1:8080/docs
```

Что проверить:

- открывается Swagger;
- присутствуют `/health`, `/parse`, `/parse/async`, `/tasks/{task_id}`.

### Шаг 4. Проверка health-check

В Swagger выполнить:

```text
GET /health
```

Ожидаемый ответ:

```json
{
  "status": "healthy"
}
```

### Шаг 5. Прямой вызов парсера

В Swagger выполнить:

```text
POST /parse
```

Тело запроса:

```json
{
  "url": "https://example.com"
}
```

Что проверить в ответе:

- присутствует URL;
- найден заголовок страницы;
- статус равен `200`;
- присутствует `id` записи в БД.

### Шаг 6. Проверка записи в PostgreSQL

Выполнить:

```powershell
docker compose exec db psql -U postgres -d finance_db -c "SELECT id, url, title, status_code, source, parsed_at FROM parsed_pages ORDER BY id DESC;"
```

Что проверить:

- появилась запись;
- поле `source` содержит `http`;
- заголовок страницы сохранён.

### Шаг 7. Постановка задачи в очередь

В Swagger выполнить:

```text
POST /parse/async
```

Тело запроса:

```json
{
  "url": "https://www.python.org"
}
```

Ожидаемый ответ:

```json
{
  "task_id": "идентификатор-задачи",
  "status": "queued"
}
```

Скопировать значение `task_id`.

### Шаг 8. Проверка статуса задачи

Выполнить:

```text
GET /tasks/{task_id}
```

Вместо `{task_id}` подставить полученный идентификатор.

Ожидаемый финальный статус:

```json
{
  "task_id": "...",
  "status": "SUCCESS",
  "result": {
    "title": "...",
    "status_code": 200
  }
}
```

### Шаг 9. Логи Celery worker

Выполнить:

```powershell
docker compose logs worker
```

Что проверить:

- worker подключён к Redis;
- задача принята;
- задача завершилась успешно.

### Шаг 10. Проверка записи Celery-задачи в PostgreSQL

Снова выполнить:

```powershell
docker compose exec db psql -U postgres -d finance_db -c "SELECT id, url, title, status_code, source, parsed_at FROM parsed_pages ORDER BY id DESC;"
```

Что проверить:

- появилась новая запись;
- поле `source` содержит `celery`.

## Запуск проекта

```powershell
docker compose up --build
```

Остановка:

```powershell
docker compose down
```

Удаление контейнеров и данных PostgreSQL:

```powershell
docker compose down -v
```

## Итог

В лабораторной работе создана Docker-система из API-шлюза, сервиса парсинга, PostgreSQL, Redis и Celery worker.

Реализованы два варианта обработки URL:

- синхронный HTTP-вызов;
- фоновый запуск через очередь задач.

Результаты обоих способов сохраняются в PostgreSQL и могут быть проверены через SQL-запрос.
