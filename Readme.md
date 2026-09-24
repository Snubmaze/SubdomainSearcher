# Утилита для поиска поддоменов домена

CLI утилита принимает домен, получает наблюдённые имена из **Subdomain API**
и отдельно проверяет их текущие IPv4 и IPv6 адреса через системный DNS-резолвер.
Для работы нужен Python 3.14+; runtime-зависимостей сверх стандартной
библиотеки нет.

## Используемое API

Для обнаружения имён используется [Subdomain API](https://subdomain.app/):
программа отправляет один GET-запрос на
`https://api.subdomain.app/v1/query?domain=google.com`. Сервис ищет ранее
замеченные поддомены в своём индексе и возвращает JSON с именем зоны,
массивом `subdomains` и счётчиками `count` и `total`. 

## Как работает поиск

1. `searcher/main.py` разбирает домен и параметры `--format` и `--save`.
   `DomainName` проверяет и нормализует введённое имя.
2. `searcher/infrastructure/subdomain_app.py` делает один HTTP-запрос к
   Subdomain API с таймаутом 10 секунд. Адаптер проверяет структуру ответа,
   принимает ответ для введённого имени или его родительской зоны, оставляет
   только корректные строгие поддомены запроса, убирает повторы и сортирует
   имена.
3. `searcher/application.py` передаёт каждое найденное имя адаптеру
   `searcher/infrastructure/dns.py`. Тот запрашивает текущие IPv4 и IPv6
   через `socket.getaddrinfo`
4. `searcher/presentation.py` превращает результат в текст или
   JSON. Если указан `--save`, CLI записывает его во временный файл в `output/`
   и затем заменяет целевой файл. При ошибке DNS частичный результат не
   выводится и старый файл не заменяется.

## Запуск без Docker

Из корня проекта:

```bash
python3.14 -m venv .venv
source .venv/bin/activate
```

Для линтинга установите Ruff:

```bash
python -m pip install -r requirements.txt
```

Полный список доступных команд:

```bash
python3 -m searcher.main <domain>
python3 -m searcher.main <domain> --format json
python3 -m searcher.main <domain> --save
python3 -m searcher.main <domain> --format json --save
```

`--format` указывает на формат вывода: текст или JSON

`--save` записывает готовый результат в `output/subdomains.txt` или
`output/subdomains.json` относительно текущей папки.

## Запуск через Docker

Для запуска нужен Docker:

```bash
docker compose build
docker compose run --rm cli <domain>
docker compose run --rm cli <domain> --format json
docker compose run --rm cli <domain> --save
docker compose run --rm cli <domain> --format json --save
```

Compose монтирует локальную папку `./output` в `/app/output`, поэтому
сохранённые файлы остаются на хосте в `output/`.

Сервис `dev` устанавливает Ruff и монтирует исходники из текущей папки.
Открыть оболочку или запустить проверки можно так:

```bash
docker compose run --rm dev
docker compose run --rm dev ruff check .
docker compose run --rm dev ruff format --check .
docker compose run --rm dev python -m unittest discover -s tests -v
```

## Пример результата

Пример для запроса `my.google.com` (адреса условные):

```text
requested_domain: my.google.com
discovered_subdomains: 2
is_truncated: true

a.my.google.com: 192.0.2.1, 2001:db8::1
b.my.google.com: N/A
```

```json
{
  "requested_domain": "my.google.com",
  "discovered_subdomains": 2,
  "is_truncated": true,
  "resolutions": [
    {
      "domain": "a.my.google.com",
      "addresses": ["192.0.2.1", "2001:db8::1"]
    },
    {
      "domain": "b.my.google.com",
      "addresses": []
    }
  ]
}
```

Для вложенного запроса API может указать в `domain` родительскую зону и
вернуть имена всей зоны. Программа принимает такой ответ, если зона является
родителем по границам DNS-меток, но выводит только **строгие поддомены
введённого имени**. Само введённое имя и соседние ветки исключаются. Для
корневого запроса правила фильтрации остаются такими же.

`is_truncated` показывает, что API сообщил о большем числе имён для
возвращённой им зоны, чем прислал в ответе.

## Ошибки и проверки

Ошибки печатаются в stderr. Код завершения `2` означает неверные аргументы или
домен, `3` — HTTP-ошибку сервера либо некорректный ответ API, `4` —
системную ошибку DNS, `5` — ошибку сохранения. Отсутствие адресов у отдельного
имени не считается сбоем: в результате будет `N/A` или `[]`.

Проверки без живой сети:

```bash
ruff check .
ruff format --check .
python -m unittest discover -s tests -v
```