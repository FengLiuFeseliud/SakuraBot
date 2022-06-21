from pycqBot.cqApi import cqBot, cqHttpApi
from pycqBot.object import Plugin, Message
from pycqBot.cqCode import node_list, image
from rssViewer import rssSubscription
from rssViewer.rssTo import rssItemToDict
from threading import Thread
import logging
import time

class rssSub(Plugin):
    
    def __init__(self, bot: cqBot, cqapi: cqHttpApi, plugin_config):
        super().__init__(bot, cqapi, plugin_config)
        self._rss = rssSubscription("./plugin/rssSub/rss_sub", "./plugin/rssSub/rss_xml")

        if plugin_config is None:
            logging.warning("not rss_group !!!")
            return

        if "rss_group" not in plugin_config:
            logging.warning("not rss_group !!!")
            return

        self.rss_group = plugin_config["rss_group"]
        self.rss_update_sleep = plugin_config["rss_update_sleep"] if "rss_update_sleep" in plugin_config else 600
        self.rss_send_name = plugin_config["rss_send_name"] if "rss_send_name" in plugin_config else "rss"
        self.rss_send_qq = plugin_config["rss_send_qq"] if "rss_send_qq" in plugin_config else "23333333"

        bot.command(self.sub, "rsssub", {

        }).command(self.unsub, "rssunsub", {

        }).command(self.rsslist, "rss", {

        })

        self._updata()

    def _rss_updata_call(self, rss_msg, rss_msg_list, rss_xml_title):
        try:
            for rss_msg in rss_msg_list:
                rss_data = rssItemToDict(rss_msg)

                if len(rss_data["img"]) == 0:
                    self.cqapi.send_group_msg(self.rss_group, "%s\n%s\n%s" % (
                        rss_xml_title,
                        rss_data["description"],
                        rss_data["link"],
                    ))
                    continue

                img_msg = ""
                for img in rss_data["img"]:
                    img_msg = "%s%s" % (img_msg, image("rss.png", img))

                self.cqapi.send_group_msg(self.rss_group, "%s\n%s\n%s\n%s" % (
                    rss_xml_title,
                    rss_data["description"],
                    img_msg,
                    rss_data["link"],
                ))

        except Exception as err:
            print(err)

    def _updata(self):
        def rss_updata():
            while True:
                self._rss.update(self._rss_updata_call)
                time.sleep(self.rss_update_sleep)

        thread = Thread(target=rss_updata, name="rss_load")
        thread.setDaemon(True)
        thread.start()

    def sub(self, cdata, message: Message):
        sub_in = self._rss.sub(cdata[0])

        if sub_in:
            message.reply("ok rss sub...")
        else:
            message.reply("sub rss err!!!")

    def unsub(self, cdata, message: Message):
        unsub_in = self._rss.unsub(cdata[0])

        if unsub_in:
            message.reply("ok rss unsub...")
        else:
            message.reply("unsub rss err!!!")
    
    def rsslist(self, cdata, message: Message):
        rss_sub_list = self._rss.sub_list()

        if not rss_sub_list:
            message.reply("rss sub == []")
            return

        self.cqapi.send_group_forward_msg(self.rss_group, node_list(rss_sub_list, self.rss_send_name, self.rss_send_qq))