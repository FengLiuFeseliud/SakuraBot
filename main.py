import asyncio
from pycqBot.cqApi import cqHttpApi, cqLog
from logging import INFO
import uvloop

cqLog(INFO)
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

cqapi = cqHttpApi()
bot = cqapi.create_bot(group_id_list=[
        685735591,
        801077724
    ],
    options={
        "admin": [
            1718089268,
        ],
        "commandSign": ""
    }
)


bot.plugin_load([
    "rssSub",
    # "pycqBot.plugin.test",
    # "pycqBot.plugin.bilibili",
    "pycqBot.plugin.pixiv",
    # "pycqBot.plugin.twitter",
    # "pycqBot.plugin.weather",
    # "pycqBot.plugin.manage",
    # "sukebei",
    "sauceNAO",
    # "blhx",
    # "imhentai",
    # "nhentai",
    # "test"
])

bot.start(start_go_cqhttp=False)
