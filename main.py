from pycqBot.cqApi import cqHttpApi, cqLog
from asyncio import set_event_loop_policy
from uvloop import EventLoopPolicy
from logging import INFO

cqLog(INFO)
set_event_loop_policy(EventLoopPolicy())

cqapi = cqHttpApi()
bot = cqapi.create_bot(group_id_list=[

    ]
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
    # "test"
])

bot.start(start_go_cqhttp=False)
