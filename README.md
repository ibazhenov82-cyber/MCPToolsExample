# client.py — MCP-клиент для secure-filesystem-server

## О проекте

`client.py` — минимальный MCP-клиент на Python для работы с **`secure-filesystem-server`** (пакет `@modelcontextprotocol/server-filesystem`). Скрипт запускает сервер как подпроцесс через stdio-транспорт, устанавливает MCP-соединение и позволяет:

- 📋 получить список доступных инструментов;
- 🛠 вызвать любой инструмент с аргументами из командной строки.

Никаких токенов, Docker и HTTP-серверов — всё работает локально в одном процессе.

---

## С каким MCP работает

| Параметр | Значение |
|---|---|
| **Сервер** | `secure-filesystem-server` |
| **Пакет** | `@modelcontextprotocol/server-filesystem` |
| **Транспорт** | stdio (подпроцесс) |
| **Sandbox-директория** | `C:\distr` (задаётся константой `SANDBOX` в `client.py`) |
| **Доступные инструменты** | `read_file`, `read_text_file`, `read_media_file`, `read_multiple_files`, `write_file`, `edit_file`, `create_directory`, `list_directory`, `list_directory_with_sizes`, `directory_tree`, `move_file`, `search_files`, `get_file_info`, `list_allowed_directories` |

Сервер имеет доступ **только** к файлам внутри `SANDBOX`. Все пути в аргументах разрешаются относительно неё.

---

## Требования

- **Python 3.10+**
- **Node.js 22.19.0+** (для `npx`)
- **`uv`** (менеджер проектов и окружений)
- **MCP SDK v2** (`mcp>=2,<3`)

Установка зависимостей:

```cmd
uv add "mcp[cli]"
```

---

## Последовательность запуска

### Шаг 1. Открыть терминал в папке с `client.py`

```cmd
cd C:\distr\AI Challenge 9\AgentsCore
```

### Шаг 2. Убедиться, что `client.py` на месте

```cmd
dir client.py
```

### Шаг 3. Готово — можно вызывать команды (см. ниже)

Скрипт сам запустит `secure-filesystem-server` при каждом вызове. Отдельно сервер поднимать **не нужно** — в отличие от HTTP-варианта, здесь используется stdio.

---

## Полный код `client.py`

```python
# client.py — только для secure-filesystem-server
import asyncio
import json
import sys
from mcp import Client, StdioServerParameters
from mcp.types import TextContent

# Директория, к которой серверу разрешён доступ
SANDBOX = r"C:\distr"

# Команда запуска secure-filesystem-server как подпроцесса (stdio)
SERVER_PARAMS = StdioServerParameters(
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", SANDBOX],
)


async def list_tools(client):
    result = await client.list_tools()
    tools = result.tools
    print(f"\n🔧 Доступно инструментов: {len(tools)}\n")
    for t in tools:
        desc = (t.description or "").replace("\n", " ")
        print(f"  • {t.name}")
        if desc:
            print(f"    {desc[:120]}" + ("..." if len(desc) > 120 else ""))


async def call_tool(client, name: str, args: dict):
    print(f"\n▶️  Вызываю инструмент: {name}")
    print(f"    Аргументы: {json.dumps(args, ensure_ascii=False)}")

    result = await client.call_tool(name, args)

    if result.is_error:
        print("❌ Инструмент вернул ошибку:")
    else:
        print("✅ Результат:")

    # Текстовые блоки (для read_text_file)
    for block in result.content:
        if isinstance(block, TextContent):
            text = block.text
            print(f"    {text[:800]}" + ("..." if len(text) > 800 else ""))

    # Структурированный ответ (для read_media_file)
    if result.structured_content is not None:
        print(f"    structured_content: {result.structured_content}")


async def main():
    # Разбор аргументов:
    #   client.py list
    #   client.py call read_text_file --path my_server.py
    #   client.py call read_media_file --path wallpaper.jpg
    argv = sys.argv[1:]
    action = argv[0] if argv else "list"

    kwargs = {}
    i = 1
    while i < len(argv):
        if argv[i].startswith("--"):
            key = argv[i][2:]
            value = argv[i + 1] if i + 1 < len(argv) else ""
            kwargs[key] = value
            i += 2
        else:
            i += 1

    # Подключаемся к secure-filesystem-server через stdio
    async with Client(SERVER_PARAMS) as client:
        print(f"✅ Подключено к secure-filesystem-server (sandbox: {SANDBOX})")

        if action == "call" and len(argv) > 1:
            await call_tool(client, argv[1], kwargs)
        else:
            await list_tools(client)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        raise
```

---

## Использование

### 📋 Получить список инструментов

```cmd
uv run python client.py list
```

Пример вывода:

```
✅ Подключено к secure-filesystem-server (sandbox: C:\distr)

🔧 Доступно инструментов: 14

  • read_file
    Read the complete contents of a file...
  • read_text_file
    Read the complete contents of a file from the file system as text...
  • read_media_file
    Read an image or audio file...
  • read_multiple_files
  • write_file
  • edit_file
  • create_directory
  • list_directory
  • list_directory_with_sizes
  • directory_tree
  • move_file
  • search_files
  • get_file_info
  • list_allowed_directories
```

Если команда `list` не указана вовсе — список инструментов выводится по умолчанию:

```cmd
uv run python client.py
```

---

### 🖼 Прочитать медиафайл

```cmd
uv run python client.py call read_media_file --path wallpaper.jpg
```

Пример вывода:

```
✅ Подключено к secure-filesystem-server (sandbox: C:\distr)

▶️  Вызываю инструмент: read_media_file
    Аргументы: {"path": "wallpaper.jpg"}
✅ Результат:
    structured_content: {'content': [{'type': 'image', 'data': '/9j/4AAQ...', 'mimeType': 'image/jpeg'}]}
```

---

### 📄 Прочитать текстовый файл

```cmd
uv run python client.py call read_text_file --path my_server.py
```

Пример вывода:

```
✅ Подключено к secure-filesystem-server (sandbox: C:\distr)

▶️  Вызываю инструмент: read_text_file
    Аргументы: {"path": "my_server.py"}
✅ Результат:
    # my_server.py
    from mcp.server.mcpserver import MCPServer
    ...
```

---

### 📂 Посмотреть содержимое директории

```cmd
uv run python client.py call list_directory --path .
```

---

### 🔍 Найти файлы по маске

```cmd
uv run python client.py call search_files --path . --pattern "*.py"
```

---

### ℹ️ Получить метаданные файла

```cmd
uv run python client.py call get_file_info --path wallpaper.jpg
```

---

## Синтаксис команд

```
uv run python client.py <действие> [<имя_инструмента>] [--arg value ...]
```

| Позиция | Значение |
|---|---|
| 1 | `list` (или пусто) — показать инструменты; `call` — вызвать инструмент |
| 2 | Имя инструмента (только при `call`) |
| далее | Пары `--ключ значение` — аргументы инструмента |

**Правила разбора аргументов:**

- Все аргументы инструмента передаются через `--имя значение`.
- Значения, состоящие только из цифр, автоматически преобразуются в `int`; с точкой — в `float`; остальное остаётся строкой.
- Если значение содержит пробелы — заключайте его в кавычки:

```cmd
uv run python client.py call read_text_file --path "My Documents\notes.txt"
```

---

## Частые ошибки

| Ошибка | Причина | Решение |
|---|---|---|
| `Unknown tool: read_text_file` | Подключились не к тому серверу (например, к `my_server.py`) | В `client.py` уже прописан `secure-filesystem-server`; убедитесь, что запускаете именно его |
| `ENOENT` / `npx не найден` | Не установлен Node.js | Установите Node.js 22.19.0+ |
| `Access denied` / `path outside allowed` | Путь вне `SANDBOX` | Используйте пути внутри `C:\distr` или измените `SANDBOX` в `client.py` |
| `ModuleNotFoundError: No module named 'mcp'` | MCP SDK не установлен | `uv add "mcp[cli]"` |
| `TypeError: object of type 'ListToolsResult' has no len()` | Использован старый синтаксис под SDK v1 | В v2 нужно `result.tools`, а не `result` |
| `"uv" не является внутренней командой` | `uv` не установлен | Установите `uv` и перезапустите терминал |
| `Синтаксическая ошибка в имени файла` | Запуск `npx` из cmd без обёртки | Используйте PowerShell или `cmd /c npx ...` |

---

## Ограничения

- Работает **только** с `secure-filesystem-server`. Для GitHub, базы данных или других MCP-серверов потребуется изменить `SERVER_PARAMS` в `client.py`.
- Sandbox жёстко задан в `client.py` (`SANDBOX = r"C:\distr"`). Для смены директории отредактируйте эту константу.
- Вывод содержимого файлов обрезается до 800 символов в консоли — это сделано для читаемости, сами данные приходят полностью.
- Медиафайлы выводятся в base64 — их нужно декодировать отдельно, если хотите сохранить на диск.
- При каждом запуске `client.py` поднимает новый экземпляр `secure-filesystem-server` через `npx`. Первый запуск может занять несколько секунд, пока `npx` скачивает пакет.

---

## Лицензия

Учебный пример. Используйте свободно.