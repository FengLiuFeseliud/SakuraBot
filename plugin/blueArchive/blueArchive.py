import os
import time
from pycqBot.cqApi import cqBot, cqHttpApi
from pycqBot.cqCode import image, node_list
from pycqBot.object import Message, Plugin

from selenium import webdriver
from selenium.webdriver.common import by
from selenium.common.exceptions import NoSuchElementException


class blueArchive(Plugin):
    """

    插件配置
    ---------------------------
    """

    def __init__(self, bot: cqBot, cqapi: cqHttpApi, plugin_config) -> None:
        super().__init__(bot, cqapi, plugin_config)
        self.__cookie = plugin_config["cookie"] if "cookie" in plugin_config else "_ga=GA1.1.507474333.1670576733; _ga_XQEWDXR13H=GS1.1.1670576732.1.1.1670577699.0.0.0; _ga_GQQY6FMTLC=GS1.1.1670576732.1.1.1670578317.0.0.0"
        self.__student_list = None 
        self.__student_alias_list = None
        
        bot.command(self.get_student, "ba学生", {
            "type": "all"
        })

    def set_cookie(self, driver):
        for data in self.__cookie.split("; "):
            name, value = data.split("=", 1)
            driver.add_cookie({
                "name": name, "value": value, "domain": ".lgc2333.top", 'path' : '/', 'secure':True, "httpOnly": False
            })

    def screenshot(self, url, file_path, path=None):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument("accept-language=zh-CN,zh;q=0.9,zh-TW;q=0.8")

        driver = webdriver.Chrome(options=options)

        driver.get(url)
        driver.execute_script("changeLanguage('Cn')")
        height = driver.execute_script("return document.body.scrollHeight")

        element = driver.find_element(by.By.XPATH, path)
        width = element.size["width"]

        driver.set_window_size(width, height)

        driver.save_screenshot(file_path)

        driver.quit()
        return "file://%s" % os.path.abspath(file_path)

    async def get_student_list(self):
        self.__student_list = await self.cqapi.link("https://schale.lgc2333.top/data/cn/students.min.json?v=69")

    async def get_student_alias(self):
        self.__student_alias_list = await self.cqapi.link("https://bawiki.lgc2333.top/data/stu_alias.json")

    async def _get_student(self, commandData, message: Message):
        if self.__student_list is None:
            await self.get_student_list()

        if self.__student_alias_list is None:
            await self.get_student_alias()

        name = None
        for key, value in  self.__student_alias_list.items():
            if key == commandData[0]:
                name = key
                break
            
            if commandData[0] in value:
                name = key

        if name is None:
            message.reply("不存在 %s 的学生..." % commandData[0])
            return

        student = None
        for data in self.__student_list:
            if data["Name"] != name:
                continue
            
            student = data["PathName"]

        file_name = "ba_student_%s.png" % commandData[0]
        message.reply_not_code(image(file_name, self.screenshot("https://schale.lgc2333.top/?chara=%s" % student, "./screenshot/%s" % file_name, '//*[@id="ba-student"]')))

    def get_student(self, commandData, message: Message):
        self.cqapi.add_task(self._get_student(commandData, message))