from pycqBot.cqApi import cqHttpApi, cqLog

cqLog()

cqapi = cqHttpApi()
bot = cqapi.create_bot()

bot.plugin_load([
    "pycqBot.plugin.bilibili",
    "pycqBot.plugin.pixiv",
    "pycqBot.plugin.twitter",
    "pycqBot.plugin.weather",
    "pycqBot.plugin.test",
    "pycqBot.plugin.manage",
    "sukebei"
])

bot.start(start_go_cqhttp=False)