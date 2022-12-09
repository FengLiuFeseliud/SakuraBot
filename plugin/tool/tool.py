import json
import logging
import os
from threading import Thread
from pycqBot.cqApi import cqBot, cqHttpApi
from pycqBot.object import Plugin, Message
from pycqBot.cqCode import image, node_list
from urllib.parse import unquote

import time

from selenium import webdriver
from selenium.webdriver.common import by
from selenium.common.exceptions import NoSuchElementException


class tool(Plugin):
    """
    插件配置
    ---------------------------

    """

    def __init__(self, bot: cqBot, cqapi: cqHttpApi, plugin_config) -> None:
        super().__init__(bot, cqapi, plugin_config)

        bot.command(self.screenshot, "网页截图", {
            "type": "all"
        })

    
    def _screenshot(self, url, message: Message):
        file_path = "./screenshot/web_screenshot.png"
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')

        driver = webdriver.Chrome(options=options)
        driver.get(url)
        height = driver.execute_script("return document.body.scrollHeight")

        message.reply("正在截图...")

        driver.set_window_size(driver.get_window_size()["width"], height)
        driver.save_screenshot(file_path)

        driver.quit()

        message.reply(image("web_screenshot.png","file://%s" % os.path.abspath(file_path)))

    def screenshot(self, commandData, message: Message):
        thread = Thread(target=self._screenshot, args=(commandData[0],message,))
        thread.setDaemon(True)
        thread.start()