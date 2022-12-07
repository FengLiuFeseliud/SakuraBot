import logging
from pycqBot.cqApi import cqBot, cqHttpApi
from pycqBot.object import Plugin, Message
from pycqBot.cqCode import node_list, image
from lxml import etree
import aiohttp

LOW_SIMILARITY = 2

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
        print(plugin_config)
        self._forward_name = plugin_config["forward_name"]
        self._forward_qq = plugin_config["forward_qq"]
        self._reply_time = plugin_config["replyTime"] if "replyTime" in plugin_config else 60

        self._headers = {
            "Cookie": plugin_config["cookie"]
        }

        bot.command(self.select, "原图", {
            "type": "all",
            "help": [
                "#原图 - 基于 sauceNAO 的 pid 搜索"
            ]
        })

    def get_data(self, html):
        """
        pixiv ID
        Creator
        Source
        """
        try:
            html = etree.HTML(html)
            if html.xpath('//div[@class="result"]') == []:
                return None
            
            if len(html.xpath('//div[@class="result"]//text()')) == 1:
                return LOW_SIMILARITY

            result = html.xpath('//div[@class="result"]')[0]
            result_img_url = result.xpath('.//div[@class="resultimage"]//img/@src')[0]
            similarity = result.xpath('.//div[@class="resultsimilarityinfo"]/text()')[0]
            title = result.xpath('.//div[@class="resulttitle"]//text()')[0]

            content = result.xpath('.//div[@class="resultcontentcolumn"]//text()')
            result_type = content[0].rstrip(": ")

            data = {
                "title": title,
                "similarity": similarity,
                "result_img_url": result_img_url,
                "result_type": result_type
            }
            if result_type == "pixiv ID":
                data["id"] = content[1]
                data["member"] = content[3]

            if result_type == "ArtStation Project":
                data["id"] = content[1]
                data["member"] = content[3]
            
            if result_type == "Source":
                data["source"] = content[1]
                data["source_url"] = result.xpath('.//div[@class="resultmiscinfo"]//a/@href')

            if result_type == "Creator(s)":
                data["creator"] = content[1:]

            if result_type not in ["pixiv ID", "Source", "Creator(s)", "ArtStation Project"]:
                data["result_type_old"] = result_type
                data["content"] = content
                data["result_type"] = "All"
                data["source_url"] = result.xpath('.//div[@class="resultmiscinfo"]//a/@href')

            return data
        except Exception as err:
            logging.exception(err)
            return True
    
    async def upload(self, code):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(code["data"]["url"]) as req:
                    data = await req.read()
                
                logging.debug("sauceNAO %s 图片流上传 saucenao API" % code["data"]["url"])
                async with session.post("https://saucenao.com/search.php", data={"file": data}, headers=self._headers) as req:
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
        
        data = self.get_data(await self.upload(image_list[0]))

        if data is None:
            message.reply("没有搜索到图片...")
            return
        
        if data is True:
            message.reply("发生未知错误, 请将该图发给我, 以复现")
            return

        if data is LOW_SIMILARITY:
            message.reply("结果相似度过低不显示")
            return

        logging.info("sauceNAO 搜索完成 %s %s %s" % (data["result_type"], data["title"], data["result_img_url"]))

        message_list = []
        message_list.append("相似度: %s" % data["similarity"])

        if data["result_type"] == "pixiv ID":
            message_list.append("pid: %s\n画师: %s" % (
                data["id"], data["member"]
            ))
            message_list.append("https://www.pixiv.net/artworks/%s" % data["id"])
        
        if data["result_type"] == "ArtStation Project":
            message_list.append("id: %s\n画师: %s" % (
                data["id"], data["member"]
            ))
            message_list.append("https://www.artstation.com/artwork/%s" % data["id"])

        if data["result_type"] == "Source":
            message_list.append("来源: %s" % data["source"])
            message_list.append("原图地址（部分网站有墙可以找没有墙的网站）:")
            for source_url in data["source_url"]:
                message_list.append(source_url)
        
        if data["result_type"] == "Creator(s)":
            message_list.append("来源:")
            for creator in data["creator"]:
                message_list.append(creator)
        
        if data["result_type"] == "All":
            message_list.append("类型: %s" % data["result_type_old"])
            message_list.append(" ".join(data["content"]))
            for source_url in data["source_url"]:
                message_list.append(source_url)
            message_list.append("这个为通用类型结果, 可以将该图发给我, 以添加支持该类型的信息")

        message_list.append("结果缩略图:")
        message_list.append(image("sauceNAO_result_img", data["result_img_url"]))
        self.cqapi.send_group_forward_msg(message.group_id, node_list(message_list, 
            self._forward_name,
            self._forward_qq
        ))
    
    def select(self, commandData, message: Message):
        # message.reply("请发送需要查找的图片！")
        message_data = self.cqapi.reply(message.user_id, self._reply_time)
        if message_data is None:
            message.reply("等待 %s 选择图超时..." % message.sender["nickname"])
            return
        
        self.cqapi.add_task(self._select(message_data))
