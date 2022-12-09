from pycqBot.cqApi import cqHttpApi, cqLog
from logging import INFO

# win
# import asyncio
# asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# linux
import asyncio, uvloop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

cqLog()

cqapi = cqHttpApi()
bot = cqapi.create_bot(group_id_list=[
        # 972057354,
        # 599694214,
        # 801077724,
        # 794710721,
        # 1030164452,
        # 453868266,
        882749965,
        467281839
    ],
    options={
        "admin": [1718089268]
    }
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
    # "traindata",
    # "bilibili",
    "blueArchive"
    # "tool"
])

bot.start()
