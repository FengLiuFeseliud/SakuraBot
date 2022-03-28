import json
import logging
import os
import time
from threading import Thread
from pycqBot.cqApi import cqBot, cqHttpApi
from pycqBot.object import Plugin, Message
from pycqBot.cqCode import image, node_list
from lxml import etree
from urllib.parse import unquote


class blhx(Plugin):
    """
    blhx wiki

    插件配置
    ---------------------------

    forward_qq: 转发使用的 qq 号
    forward_name: 转发使用的名字
    """

    def __init__(self, bot: cqBot, cqapi: cqHttpApi, plugin_config) -> None:
        super().__init__(bot, cqapi, plugin_config)
        self._ship_data_list = []
        self._forward_name = plugin_config["forward_name"]
        self._forward_qq = plugin_config["forward_qq"]
        self._reply_time = plugin_config["replyTime"] if "replyTime" in plugin_config else 60
        
        if os.path.isfile("./ship_data.json"):
            with open("./ship_data.json", "r") as file:
                self._ship_data_list = json.loads(file.read())
        else:
            cqapi.add_task(self.save_ship_data())

        bot.command(self.select, "舰船筛选", {
            "type": "all"
        })

        bot.command(self.ship, "舰船", {
            "type": "all"
        })
    
    async def save_ship_data(self):
        try:
            api = "https://wiki.biligame.com/blhx/%E5%85%A8%E8%88%B0%E8%88%B9%E7%AD%9B%E9%80%89"
            html = etree.HTML(await self.cqapi.link(api, json=False))
            flour_list = html.xpath('//div[@class="Flour"]')

            ship_data_list = []
            for flour in flour_list:
                ship_data_list.append({
                    "name": [
                        flour.xpath('.//span[@class="AF"]/text()')[0],
                        unquote(flour.xpath(".//a/@href")[0]).rsplit("/", maxsplit=1)[-1]
                    ],
                    "type": flour.xpath("./@data-particle-0")[0].split(","),
                    "camp": flour.xpath("./@data-particle-1")[0],
                    "rarity": flour.xpath("./@data-particle-2")[0],
                    "img": flour.xpath(".//img/@src")[0],
                    "url": flour.xpath(".//a/@href")[0]
                })
            
            with open("./ship_data.json", "w") as file:
                file.write(json.dumps(ship_data_list, ensure_ascii=False))

            self._ship_data_list = ship_data_list
        except Exception as err:
            logging.exception(err)
    
    def set_ship_message(self, ship_data):
        img_name = ship_data["img"].rsplit("/", maxsplit=1)[-1]
        return "%s（%s）-%s-%s-%s\n%s\nwiki: %s" % (
                ship_data["name"][1],
                ship_data["name"][0],
                ship_data["type"][0],
                ship_data["camp"],
                ship_data["type"][1],
                image(img_name, ship_data["img"]),
                "https://wiki.biligame.com%s" % ship_data["url"]
            )
        
    async def _select(self, commandData, message: Message):
        try:
            message_list = []
            for ship_data in self._ship_data_list:
                p_in = 0
                for p in commandData:
                    if p in ship_data["type"]:
                        p_in += 1
                    
                    if p == ship_data["camp"]:
                        p_in += 1
                    
                    if p == ship_data["rarity"]:
                        p_in += 1
                
                if p_in == len(commandData):
                    message_list.append(self.set_ship_message(ship_data))

            if message_list == []:
                message.reply("舰船筛选无结果...")
                return 

            if len(message_list) < 200:
                self.cqapi.send_group_forward_msg(message.group_id, node_list(message_list, 
                    self._forward_name,
                    self._forward_qq
                ))
                return
            
            self.cqapi.send_group_forward_msg(message.group_id, node_list(message_list[:200], 
                self._forward_name,
                self._forward_qq
            ))

            def send_page(message_list):
                message_data = self.cqapi.reply(message.user_id, self._reply_time)
                if message_data is None:
                    return
                
                if message_data.text != "下一页":
                    return
                
                self.cqapi.send_group_forward_msg(message.group_id, node_list(message_list, 
                    self._forward_name,
                    self._forward_qq
                ))

            thread = Thread(target=send_page, args=(message_list[200:],))
            thread.setDaemon(True)
            thread.start()

            message.reply("数据超出合并转发最大值输入 '下一页' 查看剩余")

        except Exception as err:
            logging.exception(err)

    async def _ship(self, commandData, message: Message):
        try:
            ship_name = commandData[0]
            for ship_data in self._ship_data_list:
                if ship_name not in ship_data["name"]:
                    continue
                
                break

            if ship_name not in ship_data["name"]:
                message.reply("wiki 没有 %s" % ship_name)
                return
            
            message.reply(self.set_ship_message(ship_data))
            
        except Exception as err:
            logging.exception(err)
            

    def ship(self, commandData, message: Message):
        self.cqapi.add_task(self._ship(commandData, message))
    
    def select(self, commandData, message: Message):
        self.cqapi.add_task(self._select(commandData, message))