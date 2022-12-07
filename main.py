from pycqBot.cqApi import cqHttpApi, cqLog
from logging import INFO

# win
import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# linux
# import asyncio, uvloop
# asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

cqLog(INFO)

cqapi = cqHttpApi()
bot = cqapi.create_bot(group_id_list=[

    ],
)

bot.plugin_load([
    # "rssSub",
    # "pycqBot.plugin.test",
    # "pycqBot.plugin.bilibili",
    # "pycqBot.plugin.pixiv",
    # "pycqBot.plugin.twitter",
    # "pycqBot.plugin.weather",
    # "pycqBot.plugin.manage",
    # "sukebei",
    # "sauceNAO",
    # "blhx",
    # "imhentai",
    # "nhentai",
    # "test",
    # "traindata"
])

bot.start()
