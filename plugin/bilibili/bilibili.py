import json
import logging
import os
from threading import Thread
import time
from pycqBot.cqApi import cqBot, cqHttpApi
from pycqBot.cqCode import image, node_list
from pycqBot.object import Message, Plugin

from selenium import webdriver
from selenium.webdriver.common import by
from selenium.common.exceptions import NoSuchElementException


class bilibili(Plugin):
    """
    bilibili 监听动态/直播 消息 自动解析 bilibili qq 小程序分享信息

    插件配置
    ---------------------------

    monitorLive: 监听直播 uid 列表
    monitorDynamic: 监听动态 uid 列表
    timeSleep: 监听间隔 (秒)
    """

    def __init__(self, bot: cqBot, cqapi: cqHttpApi, plugin_config) -> None:
        super().__init__(bot, cqapi, plugin_config)
        self.__monitor_live_uids = plugin_config["monitorLive"] if "monitorLive" in plugin_config else []
        self.__monitor_dynamic_uids = plugin_config["monitorDynamic"] if "monitorDynamic" in plugin_config else []
        self.__cookie = plugin_config["cookie"] if "cookie" in plugin_config else ""
        self._forward_name = plugin_config["forward_name"]
        self._forward_qq = plugin_config["forward_qq"]

        self.__dynamic_old_time: dict[int, int] = {}
        self._dynamic_monitor_in = True
        self.__send_msg_list = []
        self._threads: list[Thread] = []

        bot.timing(self.monitor_dynamic, "bilibili_monitor_dynamic", {
            "timeSleep": plugin_config["timeSleep"] if "timeSleep" in plugin_config else 30
        })

        self._headers = {
            "cookie": plugin_config["cookie"],
        }

    async def get_lives_status(self, live_list):
        return self._json_data_check(await self.cqapi.link(
                "https://api.live.bilibili.com/room/v1/Room/get_status_info_by_uids", 
                mod = "post", 
                data=json.dumps({
                    "uids": live_list
                })
            )
        )
    
    async def get_dynamic(self, uid):
        return await self.cqapi.link("https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/space_history?host_uid=%s" % uid, headers=self._headers)

    def send_dynamic(self, dynamic_data):
        try:
            send_msg = []
            dynamic_id = dynamic_data["desc"]["dynamic_id_str"]
            type_id = dynamic_data["desc"]["type"]
            rid = dynamic_data["desc"]["rid_str"]

            send_msg.append(image("dynamic_%s.png" % dynamic_id, self.screenshot_dynamic(dynamic_id)))

            item = json.loads(dynamic_data["card"])
            if "item" in item:
                item = item["item"]
            
            if "pictures" in item:
                send_msg.append([image(img_data["img_src"]) for img_data in item["pictures"]])

            if type_id == 64:
                send_msg.append(image("cv_%s.png" % rid, self.screenshot_cv(rid)))

            self.__send_msg_list.append(send_msg)
        except NoSuchElementException as err:
            logging.warning("无法找到动态 (id=%s) 元素 %s" % (dynamic_data["desc"]["dynamic_id_str"], err))
        
    
    async def _monitor_dynamic(self):
        for uid in self.__monitor_dynamic_uids:
            data = await self.get_dynamic(uid)
            if data["code"] != 0:
                logging.error("bilibili api 错误: %s" % data)
                continue

            data = data["data"]["cards"]
            if len(data) == 0:
                continue
            
            data = data[0]
            if uid not in self.__dynamic_old_time:
                self.__dynamic_old_time[uid] = data["desc"]["timestamp"]
                continue
            
            if data["desc"]["timestamp"] <= self.__dynamic_old_time[uid]:
                continue

            thread = Thread(target=self.send_dynamic, args=(data,))
            thread.setDaemon(True)
            thread.start()

            self._threads.append(thread)
            self.__dynamic_old_time[uid] = data["desc"]["timestamp"]

        self._dynamic_monitor_in = False

    def timing_jobs_start(self, job, run_count):
        if job["name"] == "bilibili_monitor_dynamic":
            self.monitor()
    
    def timing_jobs_end(self, job, run_count):
        if job["name"] == "bilibili_monitor_dynamic":
            self.monitor_send_clear()

    def monitor(self):
        self.cqapi.add_task(self._monitor_dynamic())
        while self._dynamic_monitor_in or True in [thread.is_alive() for thread in self._threads]:
            time.sleep(1)
    
    def monitor_dynamic(self, group_id):
        if len(self.__send_msg_list) > 0:
            self.cqapi.send_group_msg(group_id, "推送b站新动态!!!")

        for message_list in self.__send_msg_list:
            for message in message_list:
                if type(message) is list:
                    self.cqapi.send_group_forward_msg(group_id, node_list(message, 
                        self._forward_name,
                        self._forward_qq
                    ))
                    continue

                self.cqapi.send_group_msg(group_id, message)

    def monitor_send_clear(self):
        if len(self.__send_msg_list) != 0:
            logging.info("bilibili: 监听到了 %s 条新动态" % len(self.__send_msg_list))

        self._threads = []
        self.__send_msg_list = []
        self._dynamic_monitor_in = True

    def set_cookie(self, driver):
        for data in self.__cookie.split("; "):
            name, value = data.split("=", 1)
            driver.add_cookie({
                "name": name, "value": value, "domain": ".bilibili.com", 'path' : '/', 'secure':True, "httpOnly": False
            })
    
    def screenshot(self, url, file_path, path=None):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')

        driver = webdriver.Chrome(options=options)
        driver.maximize_window()

        driver.get(url)
        self.set_cookie(driver)
        driver.get(url)
        time.sleep(1)

        width = driver.execute_script("return document.body.scrollWidth")
        height = driver.execute_script("return document.body.scrollHeight")

        driver.set_window_size(width, height)
        if path is None:
            print("页面长度 %sx%s " % (width, height))
            driver.save_screenshot(file_path)

        else:
            driver.find_element(by.By.XPATH, path).screenshot(file_path)

        driver.quit()
        return "file://%s" % os.path.abspath(file_path)
    
    def screenshot_dynamic(self, dynamic_id):
        file_path = "./screenshot/dynamic_%s.png" % dynamic_id
        return self.screenshot("https://t.bilibili.com/%s" % dynamic_id, file_path, '//*[@id="app"]/div[2]/div/div/div[1]')

    def screenshot_cv(self, cv_id):
        file_path = "./screenshot/cv_%s.png" % cv_id
        return self.screenshot("https://www.bilibili.com/read/cv%s" % cv_id, file_path, '//*[@id="app"]/div/div[3]/div[1]')
