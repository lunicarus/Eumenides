
import asyncio
from app.workers.crawler import run_crawl
from telethon import TelegramClient
import os
from app.config import settings

from telethon import functions

async def search_and_crawl(keyword: str, limit: int = 20):
    session_name = os.environ.get("TELEGRAM_CRAWLER_SESSION", "crawler_session")
    client = TelegramClient(session_name, settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH)
    await client.start()
    result = await client(functions.contacts.SearchRequest(
        q=keyword,
        limit=limit
    ))
    handles = []
    for user in result.users:
        if hasattr(user, 'username') and user.username:
            handles.append(user.username)
    print(f"Found handles: {handles}")
    await run_crawl(handles)





if __name__ == "__main__":
    manual_handles = [
        "cpselq0", "cpselq1"#, "cpselq2", "cpselq3", "cpselq4", "cpselq5", "cpselq6", "cpselq7", "cpselq8", "cpselq9","hotlinkse","hotlinkso"
    ]
    keywords = [
        "cpsel", "vendo_cp", #"kidspor","hotlinks" 
    ]  # Add as many as you want
    delay_seconds = 30  # Big delay between keyword searches
    safe_handles = [
        "kidsport", "kidsportschool" # Add any handles you want to exclude
    ]

    async def combined_crawl():
        session_name = os.environ.get("TELEGRAM_CRAWLER_SESSION", "crawler_session")
        client = TelegramClient(session_name, settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH)
        await client.start()
        keyword_handles = set()
        for keyword in keywords:
            print(f"Searching for keyword: {keyword}")
            result = await client(functions.contacts.SearchRequest(q=keyword, limit=10))
            found = [user.username for user in result.users if hasattr(user, 'username') and user.username]
            print(f"Handles found for '{keyword}': {found}")
            keyword_handles.update(found)
            await asyncio.sleep(delay_seconds)
        all_handles = list((set(manual_handles) | keyword_handles) - set(safe_handles))
        print(f"Combined handles (excluding safe): {all_handles}")
        await run_crawl(all_handles)

    asyncio.run(combined_crawl())
