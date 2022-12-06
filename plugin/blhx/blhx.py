import json
import logging
import os
from threading import Thread
from pycqBot.cqApi import cqBot, cqHttpApi
from pycqBot.object import Plugin, Message
from pycqBot.cqCode import image, node_list
from lxml import etree
from urllib.parse import unquote


class blhx(Plugin):
    """
    碧蓝航线 wiki

    插件配置
    ---------------------------

    forward_qq: 转发使用的 qq 号
    forward_name: 转发使用的名字
    replyTime: 等待下一页时长 单位秒 默认 60
    """

    def __init__(self, bot: cqBot, cqapi: cqHttpApi, plugin_config) -> None:
        super().__init__(bot, cqapi, plugin_config)
        self._forward_name = plugin_config["forward_name"]
        self._forward_qq = plugin_config["forward_qq"]
        self._reply_time = plugin_config["replyTime"] if "replyTime" in plugin_config else 60

        bot.command(self.ship_select, "舰船筛选", {
            "type": "all"
        })

        bot.command(self.ship, "舰船", {
            "type": "all"
        })

        bot.command(self.equipment_select, "装备筛选", {
            "type": "all"
        })

        bot.command(self.equipment_fall, "装备掉落", {
            "type": "all"
        })

        bot.command(self.equipment, "装备", {
            "type": "all"
        })
    
    async def get_ship_data(self):
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
            
            return ship_data_list
        except Exception as err:
            logging.error("blhx 获取舰船 error: %s" % err)
            logging.exception(err)
    
    async def get_equipment_data(self, equipment_type):
        try:
            api = "https://wiki.biligame.com/blhx/%s" % equipment_type
            html = etree.HTML(await self.cqapi.link(api, json=False))
            tr_list = html.xpath('//*[@id="CardSelectTr"]/tbody/tr')

            equipment_data_list = []
            for tr in tr_list[1:]:
                td_list = tr.xpath("./td")
                
                data = [td_list[0].xpath(".//text()")[0]]
                for td in td_list[1:-1]:
                    text_list = td.xpath(".//text()")
                    if len(text_list) == 1:
                        data.append(text_list[0])
                    else:
                        # 设备
                        data.append(" ".join(text_list))
                
                fall_data_list = td_list[-1].xpath(".//text()")
                if len(fall_data_list) == 1:
                    fall_data_list[0] = ""
                else:
                    for index, text in enumerate(fall_data_list):
                        if text == "：" and index > 2:
                            fall_data_list[index-2] += "\n"
                        
                data.append("".join(fall_data_list))
                equipment_data_list.append({
                    "name": data[0],
                    "type": tr.xpath('./@data-param1')[0],
                    "camp": ",".join(tr.xpath('./@data-param3')),
                    "rarity": tr.xpath('./@data-param2')[0],
                    "img": tr.xpath('.//*[@class="xtb-image"]//img/@src')[0],
                    "data": data[1:],
                    "url": tr.xpath('.//*[@class="xtb-image"]/a/@href')[0],
                })
            
            return equipment_data_list
        except Exception as err:
            logging.error("blhx 获取装备 error: %s" % err)
            logging.exception(err)
    
    def set_ship_message(self, ship_data):
        img_name = ship_data["img"].rsplit("/", maxsplit=1)[-1]
        return "%s（%s）-%s-%s-%s-%s\n%s\nwiki: %s" % (
                ship_data["name"][1],
                ship_data["name"][0],
                ship_data["type"][0],
                ship_data["camp"],
                ship_data["type"][1],
                ship_data["rarity"],
                image(img_name, ship_data["img"]),
                "https://wiki.biligame.com%s" % ship_data["url"]
            )
    
    def set_log_message(self, equipment_data, equipment_big_type):
        
        if equipment_big_type == "鱼雷":
            return "伤害：%s强满伤害：%s标准射速：%s强满射速：%s雷击：%s弹药：%s索敌范围：%s索敌角度：%s弹药射程：%s散布角度：%s" % (
                equipment_data["data"][0],
                equipment_data["data"][1],
                equipment_data["data"][2],
                equipment_data["data"][3],
                equipment_data["data"][4],
                equipment_data["data"][5],
                equipment_data["data"][6],
                equipment_data["data"][7],
                equipment_data["data"][8],
                equipment_data["data"][9],
            )
        
        if equipment_big_type == "防空炮":
            return "伤害：%s强满伤害：%s标准射速：%s强满射速：%s索敌范围：%s散布：%s防空：%s命中：%s炮击：%s特性：%s索敌角度：%s弹药：%s" % (
                equipment_data["data"][0],
                equipment_data["data"][1],
                equipment_data["data"][2],
                equipment_data["data"][3],
                equipment_data["data"][4],
                equipment_data["data"][5],
                equipment_data["data"][6],
                equipment_data["data"][7],
                equipment_data["data"][8],
                equipment_data["data"][9],
                equipment_data["data"][10],
                equipment_data["data"][11],
            )
        
        if equipment_big_type == "设备":
            return "属性1：%s\n属性2：%s\n属性3：%s\n属性4：%s" % (
                equipment_data["data"][0],
                equipment_data["data"][1],
                equipment_data["data"][2],
                equipment_data["data"][3],
            ), "技能：%s" % equipment_data["data"][4]
        
        if equipment_big_type in ["舰炮", "驱逐炮", "重巡炮", "大口径重巡炮", "战列炮", "絮库夫炮"]:
            return "类型：%s伤害：%s强满伤害：%s伤害补正：%s标准射速：%s强满射速：%s炮击：%s防空：%s特性：%s弹药：%s" % (
                equipment_data["data"][0],
                equipment_data["data"][1],
                equipment_data["data"][2],
                equipment_data["data"][3],
                equipment_data["data"][4],
                equipment_data["data"][5],
                equipment_data["data"][6],
                equipment_data["data"][7],
                equipment_data["data"][8],
                equipment_data["data"][9]
            ), "索敌范围：%s索敌角度：%s弹药射程：%s" % (
                equipment_data["data"][10],
                equipment_data["data"][11],
                equipment_data["data"][12]
            )

        if equipment_big_type in ["舰载机", "轰炸机", "战斗机", "鱼雷机", "水上机"]:
            return "类型：%s标准射速：%s强满射速：%s航空：%s特性：%s舰载机航速：%s回避上限(百分比)：%s" % (
                equipment_data["data"][0],
                equipment_data["data"][1],
                equipment_data["data"][2],
                equipment_data["data"][3],
                equipment_data["data"][4],
                equipment_data["data"][5],
                equipment_data["data"][6]
            )
    
    def set_equipment_message(self, equipment_data, equipment_type):
        try:
            img_name = equipment_data["img"].rsplit("/", maxsplit=1)[-1]
            return '%s-%s-%s-%s\n%s\n查看掉落 #装备掉落 %s %s' % (
                equipment_data["name"],
                equipment_data["type"],
                equipment_data["camp"],
                equipment_data["rarity"],
                image(img_name, equipment_data["img"]),
                equipment_type,
                equipment_data["name"],
            ), self.set_log_message(equipment_data, equipment_type)
        except Exception as err:
            logging.exception(err)
    
    def send_page(self, message, message_list):
        def _send_page(message, message_list, count=None, page_in=False):
            if count is None:
                count = 0
                
            if len(message_list) > count + 200:
                message.reply("数据超出合并转发最大值输入 '下一页' 查看剩余")
                
                stat = count if page_in else 0
                self.cqapi.send_group_forward_msg(message.group_id, node_list(message_list[stat:count + 200], 
                    self._forward_name,
                    self._forward_qq
                ))

                message_data = self.cqapi.reply(message.user_id, self._reply_time)
                if message_data is None:
                    return
                
                if message_data.text != "下一页":
                    return
                
                _send_page(message, message_list, count + 200, page_in=True)

            else:
                self.cqapi.send_group_forward_msg(message.group_id, node_list(message_list[count:], 
                    self._forward_name,
                    self._forward_qq
                ))
                return
                

        thread = Thread(target=_send_page, args=(message, message_list,))
        thread.setDaemon(True)
        thread.start()
        
    async def _ship_select(self, commandData, message: Message):
        try:
            ship_data_list = await self.get_ship_data()
            if ship_data_list == []:
                return

            message_list = []
            for ship_data in ship_data_list:
                if not await self.wiki_select(commandData, ship_data):
                    continue

                message_list.append(self.set_ship_message(ship_data))

            logging.info("舰船筛选 %s 结果 count %s" % (commandData, len(message_list)))
            if message_list == []:
                message.reply("舰船筛选无结果...")
                return 
            
            self.send_page(message, message_list)

        except Exception as err:
            message.reply("发生错误！%s" % err)

            logging.error("blhx 舰船筛选 error: %s" % err)
            logging.exception(err)
    
    async def wiki_data_ck(self, name, data_list, message):
        for data in data_list:
            if name not in data["name"]:
                continue
            
            break

        if name not in data["name"]:
            message.reply("wiki 没有 %s" % name)
            return None
        
        return data
    
    async def wiki_select(self, commandData, data):
        if commandData == []:
            return True

        p_in = 0
        for p in commandData:
            if p in data["type"]:
                p_in += 1
            
            if p == data["camp"]:
                p_in += 1
            
            if p == data["rarity"]:
                p_in += 1
            
        if p_in == len(commandData):
            return True
        
        return False

    async def _ship(self, commandData, message: Message):
        try:
            ship_name = commandData[0]
            ship_data_list = await self.get_ship_data()
            if ship_data_list == []:
                return

            ship_data = await self.wiki_data_ck(ship_name, ship_data_list, message)
            if ship_data is None:
                return
            
            message.reply(self.set_ship_message(ship_data))
            
        except Exception as err:
            message.reply("发生错误！%s" % err)

            logging.error("blhx 舰船 error: %s" % err)
            logging.exception(err)
    
    async def _equipment_select(self, commandData, message: Message):
        try:
            equipment_data_list = await self.get_equipment_data(commandData[0])

            message_list = []
            for equipment_data in equipment_data_list:
                if not await self.wiki_select(commandData[1:], equipment_data):
                    continue

                for equipment_message in self.set_equipment_message(equipment_data, commandData[0]):
                    if type(equipment_message) is not tuple:
                        message_list.append(equipment_message)
                        continue
                    
                    for equipment_s_message in equipment_message:
                        message_list.append(equipment_s_message)

            logging.info("装备筛选 %s 结果 count %s" % (commandData, len(message_list)))
            if message_list == []:
                message.reply("装备筛选无结果...")
                return 

            self.send_page(message, message_list)
        except Exception as err:
            message.reply("发生错误！%s" % err)

            logging.error("blhx 装备筛选 error: %s" % err)
            logging.exception(err)

    async def _equipment_select_one(self, commandData, message: Message):
        equipment_name = commandData[1]
        equipment_data_list = await self.get_equipment_data(commandData[0])
        if equipment_data_list == []:
            return
        
        equipment_data = await self.wiki_data_ck(equipment_name, equipment_data_list, message)
        if equipment_data is None:
            return
        
        return equipment_data

    async def _equipment_fall(self, commandData, message: Message):
        try:
            equipment_data = await self._equipment_select_one(commandData, message)
            fall_data = equipment_data["data"][-1]
            self.cqapi.send_group_forward_msg(message.group_id, node_list(fall_data.split("\n"), 
                self._forward_name,
                self._forward_qq
            ))
        except Exception as err:
            message.reply("发生错误！%s" % err)

            logging.error("blhx 装备掉落 error: %s" % err)
            logging.exception(err)

    async def _equipment(self, commandData, message: Message):
        try:
            equipment_data = await self._equipment_select_one(commandData, message)
            
            for equipment_message in self.set_equipment_message(equipment_data, commandData[0]):
                if type(equipment_message) is not tuple:
                    message.reply(equipment_message)
                    continue
                
                for equipment_s_message in equipment_message:
                    message.reply(equipment_s_message)
        except Exception as err:
            message.reply("发生错误！%s" % err)

            logging.error("blhx 装备 error: %s" % err)
            logging.exception(err)

    def ship_select(self, commandData, message: Message):
        self.cqapi.add_task(self._ship_select(commandData, message))
    
    def ship(self, commandData, message: Message):
        self.cqapi.add_task(self._ship(commandData, message))

    def equipment_select(self, commandData, message: Message):
        self.cqapi.add_task(self._equipment_select(commandData, message))
    
    def equipment_fall(self, commandData, message: Message):
        self.cqapi.add_task(self._equipment_fall(commandData, message))

    def equipment(self, commandData, message: Message):
        self.cqapi.add_task(self._equipment(commandData, message))