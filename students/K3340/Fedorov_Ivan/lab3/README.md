# Лабораторная работа 3: Docker, источники данных и очереди

## Что реализовано

- PostgreSQL для данных лабораторной работы;
- отдельный FastAPI-сервис парсера с HTTP-методом `POST /parse`;
- FastAPI API-шлюз, который вызывает парсер от имени клиента;
- Celery worker для фонового запуска парсера через Redis;
- Dockerfile для API, парсера и worker;
- `docker-compose.yml` для запуска PostgreSQL, Redis, API, парсера и Celery worker.

## Состав сервисов

| Сервис | Порт | Назначение |
| --- | ---: | --- |
| `api` | `8080` | Принимает клиентские запросы и вызывает парсер напрямую или через очередь |
| `parser` | `8001` | Загружает HTML, извлекает `<title>`, сохраняет результат в PostgreSQL |
| `worker` | - | Выполняет задачи Celery в фоне |
| `redis` | `6379` | Брокер сообщений и backend результатов Celery |
| `db` | `5433` | PostgreSQL с таблицей `parsed_pages` |

## Запуск

```bash
cd students/K3340/Fedorov_Ivan/lab3
docker compose up --build
```

Документация API:

- API-шлюз: <http://127.0.0.1:8080/docs>
- parser service: <http://127.0.0.1:8001/docs>

## Проверка прямого вызова парсера

```bash
curl -X POST http://127.0.0.1:8080/parse \
  -H "Content-Type: application/json" \
  -d "{\"url\":\"https://example.com\"}"
```

API принимает URL, отправляет запрос в контейнер `parser`, получает результат и возвращает его клиенту.

## Проверка вызова через очередь

```bash
curl -X POST http://127.0.0.1:8080/parse/async \
  -H "Content-Type: application/json" \
  -d "{\"url\":\"https://example.com\"}"
```

Ответ содержит `task_id`. Статус задачи:

```bash
curl http://127.0.0.1:8080/tasks/<task_id>
```

## Где сохраняются данные

Парсер и Celery worker сохраняют результаты в PostgreSQL:

```sql
SELECT url, title, status_code, source, parsed_at, error
FROM parsed_pages
ORDER BY id DESC;
```

Поле `source` показывает способ запуска:

- `http` - прямой вызов parser service;
- `celery` - фоновый запуск через очередь.

