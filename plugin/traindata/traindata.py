from pycqBot.cqApi import cqBot, cqHttpApi
from pycqBot.object import Plugin, Message

import aiofiles
import logging
import os


class traindata(Plugin):
    """

    插件配置
    ---------------------------


    """

    def __init__(self, bot: cqBot, cqapi: cqHttpApi, plugin_config) -> None:
        super().__init__(bot, cqapi, plugin_config)
        self.__save_path = plugin_config["save_path"] if "save_path" in plugin_config else "./plugin/traindata/train"
        self.__save_time = plugin_config["save_time"] if "save_time" in plugin_config else 60 * 2
        self.__old_time = {}
        self.__size = 0
        self.__file_count = 0

        self.ck_dir()

        bot.command(self.status, "语料", {
            "type": "all",
            "admin": True
        })

    def ck_dir(self):
        if not os.path.exists(self.__save_path):
            os.makedirs(self.__save_path)

        size = 0
        file_count = 0
        for file in os.listdir(self.__save_path):
            file_path = os.path.join(self.__save_path, file)
            if os.path.isdir(file_path):
                continue

            file_count += 1
            size += os.path.getsize(file_path)

        self.__size = size
        self.__file_count = file_count
                

    async def wtrain(self, data, group_id):
        self.ck_dir()
        file_path = os.path.join(self.__save_path, "train_%s.txt" % group_id)

        mode = "a"
        if not os.path.exists(file_path):
            mode = "w"

        async with aiofiles.open(file_path, mode, encoding="utf8") as file:
            await file.write(data)
    
    async def wtrain_fun(self, message: Message):
        text = message.text
        for str in message.code_str:
            text = text.replace(str, "", 1)

        if text == "":
            return
            
        if message.group_id not in self.__old_time:
            await self.wtrain("\n", message.group_id)
            self.__old_time[message.group_id] = message.time
        
        if message.time - self.__old_time[message.group_id] > self.__save_time:
            logging.info("开始记录新的一段闲聊 group_id: %s" % message.group_id)
            await self.wtrain("\n", message.group_id)

        await self.wtrain("%s\n" % text, message.group_id)
        logging.info("记录闲聊 text: %s group_id: %s" % (text, message.group_id))
        self.__old_time[message.group_id] = message.time

    def on_group_msg(self, message: Message):
        self.cqapi.add_task(self.wtrain_fun(message))

    def status(self, commandData, message: Message):
        message.reply("语料采集状态\n群数: %s\n语料大小: %smd\n最后聊天记录超过 %ss 语料新一段\n语料目录: %s" % (self.__file_count, round(self.__size / 1048576, 3), self.__save_time, self.__save_path))
    