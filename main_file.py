"""
Name   : URL Cleaner Bot
Author : Agneev Mukherjee

"""
import logging
import re
from telethon.errors.rpcerrorlist import ChatWriteForbiddenError, SlowModeWaitError
from telethon.sync import TelegramClient, events
from telethon.tl.custom import Button
from telethon.tl.types import MessageEntityUrl, MessageEntityTextUrl, User
from unalix import clear_url

from CONFIG import api_hash, api_id, bot_token

logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s",
    level=logging.ERROR,
    filename="logs.log",
)

bot = TelegramClient("bot", api_id, api_hash).start(bot_token=bot_token)
url_re = re.compile(
    r"(([hHtTpP]{4}[sS]?)://)?([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?"
)


@bot.on(events.NewMessage(pattern=r"/start"))
async def start_hndlr(event):
    await event.reply(
        """
🧹 I will get you clean URLs without any tracking data using the Unalix library.

You can send multiple URLs in one message/one inline query as well with newline or space as separator.

❔ How to use?
1. Forward me any message with links, I will reply you with clean URLs
2. Add me to your group, I will reply the messages with clean URLs
3. Use me in inline as well (but limited to 255 chars)

PS: Promote me as admin, if you have enabled slow mode in group
""",
        buttons=[
            Button.url(
                "📝 Source", "https://github.com/agneevX/url-cleaner-bot"
            )
        ],
    )
    raise events.StopPropagation


@bot.on(events.NewMessage(incoming=True))
async def clearurl_hndlr(event):
    if event.message.via_bot is not None:  # Don't handle inline messages by other bots
        return
    if event.message.entities:
        to_send = set()
        input_urls = set()
        for input_url in url_re.finditer(event.message.text):
            found = input_url.group()
            if len(found) > 10:  # to filter false-positives (decimal numbers are mistaken as urls)
                input_urls.add(found)

        #  Get url from formatted entities
        for entity in event.message.entities:
            if isinstance(entity, MessageEntityTextUrl):
                input_urls.add(entity.url)

        if input_urls:
            for url in input_urls:
                try:
                    clean_url = clear_url(url)
                    if url != clean_url:
                        to_send.add(clean_url)
                except Exception as e:
                    logging.error(f"{e} - URL: {url}")

        if to_send:
            to_send_txt = "\n\n".join(i for i in to_send)
            try:
                await event.reply(
                    f"🧹 Clean URL: \n{to_send_txt}", link_preview=False
                )
            except ChatWriteForbiddenError:
                # bot could send to the user (who added this bot to group), since we are not storing any details,
                # the only way to handle is to ignore
                pass
            except SlowModeWaitError:  # FIXME schedule the msg to be sent after wait period
                pass

        else:
            chat = await event.get_chat()
            if isinstance(
                chat, User
            ):  # don't disturb the group, only show at private chat
                await event.reply("No unclean links found!")
    else:
        chat = await event.get_chat()
        if isinstance(
            chat, User
        ):  # don't disturb the group, only throw error at private chat
            await event.reply("The message did not contain any links for me to clean!")
    raise events.StopPropagation


@bot.on(events.InlineQuery)
async def handler(event):
    builder = event.builder
    input_urls = []
    if "\n" in event.text:
        input_urls.extend(event.text.split("\n"))
    # if no new line found, (i.e) just one link
    if len(event.text) and not input_urls:
        input_urls = [event.text]

    if input_urls:
        result = "\n".join(clear_url(link) for link in input_urls)
    else:
        result = "No URLs found"
    await event.answer(
        [builder.article("🧹 Cleaned URLs", text=result, link_preview=False)]
    )


bot.run_until_disconnected()
