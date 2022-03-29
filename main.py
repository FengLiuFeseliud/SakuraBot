from pycqBot.cqApi import cqHttpApi, cqLog

cqLog()

cqapi = cqHttpApi()
bot = cqapi.create_bot()

bot.plugin_load([
    "pycqBot.plugin.test",
    "pycqBot.plugin.bilibili",
    "pycqBot.plugin.pixiv",
    "pycqBot.plugin.twitter",
    "pycqBot.plugin.weather",
    "pycqBot.plugin.manage",
    "sukebei",
    "sauceNAO",
    "blhx",
    "nhentai"
])

bot.start(start_go_cqhttp=False)