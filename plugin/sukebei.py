import logging
import time
from lxml import etree
from pycqBot.cqApi import cqBot, cqHttpApi
from pycqBot.object import Plugin, Message
from pycqBot.cqCode import node_list


class sukebei(Plugin):
    """
    基于 sukebei 的磁力链接搜索

    插件配置
    ---------------------------
    
    forward_qq: 转发使用的 qq 号
    forward_name: 转发使用的名字
    proxy: 代理 ip
    maxLen: 显示磁力链接条数 默认 10
    maxReplyCount: 最大错误序号重试次数 默认 3
    replyTime: 等待选择磁力链接时长 单位秒 默认 60
    """

    def __init__(self, bot: cqBot, cqapi: cqHttpApi, plugin_config):
        super().__init__(bot, cqapi, plugin_config)
        self.__magnet_list = {}
        self._max_len = plugin_config["maxLen"] if "maxLen" in plugin_config else 10
        self._max_reply_count = plugin_config["maxReplyCount"] if "maxReplyCount" in plugin_config else 3
        self._reply_time = plugin_config["replyTime"] if "replyTime" in plugin_config else 60
        self._forward_name = plugin_config["forward_name"]
        self._forward_qq = plugin_config["forward_qq"]
        self._proxy = ("http://%s" % plugin_config["proxy"]) if "proxy" in plugin_config else None

        bot.command(self.magnet, "磁链", {
            "type": "all"
        })
    
    async def get_magnet(self, q):
        try:
            api = "https://sukebei.nyaa.si/?f=0&c=0_0&q=%s&s=seeders&o=desc" % q
            html = await self.cqapi.link(api, json=False, proxy=self._proxy)
            html = etree.HTML(html)
            
            magnet_list = []
            tbody = html.xpath('//div[@class="table-responsive"]/table/tbody')[0]
            for tr in tbody.xpath('.//tr'):
                td= tr.xpath("./td")
                magnet_list.append({
                    "title": td[1].xpath('./a/text()')[-1],
                    "url": "https://sukebei.nyaa.si%s" % td[1].xpath('./a/@href')[0],
                    "magnet": td[2].xpath('./a/@href')[-1],
                    "size": td[3].xpath('./text()')[0],
                    "seeding": td[5].xpath('./text()')[0],
                    "leechers": td[6].xpath('./text()')[0],
                    "completed_downloads": td[7].xpath('./text()')[0],
                })
            
            return magnet_list[:self._max_len]
        except Exception as err:
            logging.error("sukebei 搜索失败 error: %s" % err)
            logging.exception(err)
        
        return None

    async def _magnet(self, q, message: Message):
        magnet_list = await self.get_magnet(q)
        if magnet_list is None:
            self.__magnet_list[message.user_id] = None
            return

        message_list = ["等待 %s 选择磁力链接，发送序号查看" % message.sender["nickname"]]
        for index, magnet in enumerate(magnet_list):
            message_list.append("%s.%s 做种数：%s " % (index, 
                    magnet["title"][:40], 
                    magnet["seeding"], 
                )
            )

        self.cqapi.send_group_forward_msg(message.group_id, node_list(message_list, 
            self._forward_name,
            self._forward_qq
        ))

        self.__magnet_list[message.user_id] = magnet_list

    def magnet(self, commandData, message: Message):
        self.cqapi.add_task(self._magnet(commandData[0], message))

        while message.user_id not in self.__magnet_list:
            time.sleep(1)

        if self.__magnet_list[message.user_id] is None:
            self.__magnet_list.pop(message.user_id)
            return

        reply_count = 0
        while reply_count < self._max_reply_count:
            reply_count += 1
            
            message_data = self.cqapi.reply(message.user_id, self._reply_time)
            if message_data is None:
                message.reply("等待 %s 选择磁力链接超时..." % message.sender["nickname"])
                return

            magnet_index = int(message_data.text)
            if magnet_index > len(self.__magnet_list[message.user_id]) or magnet_index < 0:
                if reply_count == self._max_reply_count:
                    message.reply("错误次数过多，中止输入")
                    return

                message.reply("错误的序号 %s，请重新输入" % magnet_index)
                continue
            
            break

        message.reply(self.__magnet_list[message.user_id][magnet_index]["magnet"])
        self.__magnet_list.pop(message.user_id)