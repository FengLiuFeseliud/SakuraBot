import logging
from pycqBot.cqApi import cqBot, cqHttpApi
from pycqBot.object import Plugin, Message
from lxml import etree
import aiohttp


class sauceNAO(Plugin):
    """
    基于 sauceNAO 的 pid 搜索
    https://saucenao.com/

    插件配置
    ---------------------------

    proxy: 代理 ip
    replyTime: 等待选择图时长 单位秒 默认 60
    """

    def __init__(self, bot: cqBot, cqapi: cqHttpApi, plugin_config) -> None:
        super().__init__(bot, cqapi, plugin_config)
        self._proxy = ("http://%s" % plugin_config["proxy"]) if "proxy" in plugin_config else None
        self._reply_time = plugin_config["replyTime"] if "replyTime" in plugin_config else 60

        bot.command(self.select, "原图", {
            "type": "all",
            "help": [
                "#原图 - 基于 sauceNAO 的 pid 搜索"
            ]
        })

    def get_data(self, html):
        html = etree.HTML(html)
        if html is None:
            return (None, None, None)

        data = html.xpath('//a[@class="linkify"]/text()')
        if not data:
            return (None, None, None)

        img_id, member = data[0:2]
        title = html.xpath('//div[@class="resulttitle"]//text()')[0]
        return img_id, member, title
    
    async def upload(self, code):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(code["data"]["url"]) as req:
                    data = await req.read()
                
                logging.debug("sauceNAO %s 图片流上传 saucenao API" % code["data"]["url"])
                async with session.post("https://saucenao.com/search.php", data={"file": data}, proxy=self._proxy) as req:
                    return await req.text()

        except Exception as err:
            logging.error("sauceNAO %s 图片流上传失败" % code["data"]["url"])
            logging.exception(err)
    
    async def _select(self, message: Message):
        image_list = []
        for code in message.code:
            if code["type"] == "image":
                image_list.append(code)
        
        if image_list == []:
            message.reply("没有输入图片...")
            return

        if len(image_list) > 1:
            message.reply("超过一张图片，只用第一张图片")
        
        img_id, member, title = self.get_data(await self.upload(image_list[0]))
        logging.info("sauceNAO 搜索完成 %s %s %s" % (img_id, member, title))
        if img_id is None:
            message.reply("没有搜索到图片...")
            return

        # 不稳定
        # message.reply("%s\n%s\npid: %s\nurl: %s" % (
        #     title, member, img_id, "https://www.pixiv.net/artworks/%s" % img_id
        # ))

        message.reply("pid: %s\nurl: %s" % (
            img_id, "https://www.pixiv.net/artworks/%s" % img_id
        ))
    
    def select(self, commandData, message: Message):
        message.reply("请发送需要查找的图片！")
        message_data = self.cqapi.reply(message.user_id, self._reply_time)
        if message_data is None:
            message.reply("等待 %s 选择图超时..." % message.sender["nickname"])
            return
        
        self.cqapi.add_task(self._select(message_data))
