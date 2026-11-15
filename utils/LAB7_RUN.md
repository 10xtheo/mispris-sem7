# Запуск и демонстрация №7

Из корня проекта в Python-окружении с установленным requirements.txt:

```bash
python scripts/lab7_demo.py
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/mispris_lab7_demo \
  uvicorn src.main:app --host 0.0.0.0 --port 8007
```

`lab7_demo.py` создаёт/восстанавливает выделенную базу `mispris_lab7_demo`; данные этой базы заменяются. Существующая рабочая `mispis_sem7` не используется. Доступ к PostgreSQL соответствует настройкам учебного стенда предыдущих работ.

- Swagger №7: http://localhost:8007/docs/lab7
- Документ заказа: http://localhost:8007/api/configuration/orders/1
- Печать / PDF: http://localhost:8007/api/configuration/orders/1/print
- Себестоимость: http://localhost:8007/api/configuration/orders/1/cost?pricelist_set_id=1
- Приёмка: `python scripts/acceptance_lab7.py`; протоколы в `utils/lab7/protocols` (путь можно задать через LAB7_PROTOCOL_DIR).
- Автотесты: `TEST_DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/mispris_lab7_test pytest`. Указанная тестовая БД и её `_migr`-вариант пересоздаются.

Методы задания: GET_CONFIG_PARAMS → config_params, CREATE_VARIANT → create_variant, ADD_TO_ORDER → put_position, CHECK_CONSTRAINTS → check_constraints, EVAL_FUNCTION → ConstraintInterpreter.evaluate.

Сценарий: получить параметры шаблона 22, проверить неверное сочетание 35 см / 100 г сыра / добавка 18, создать допустимый вариант 30 см / 130 г / 18, вывести заказ 1, показать калькуляцию 628,25 рубля, согласовать заказ и проверить блокировку правки.

Сидер содержит два конкретных варианта с собственными технологическими маршрутами. Новый вариант, созданный через API, получает значения параметров, но производственный маршрут необходимо назначить отдельно операциями №6 — приложение не подставляет стоимость шаблона автоматически.

Новая модель состоит из семи таблиц миграции 004. Узлы выражений функций хранятся JSONB, их структура, ссылки и типы проверяются сервисом до сохранения. Связь вызова с определением по коду не является SQL FK.
