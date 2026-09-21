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