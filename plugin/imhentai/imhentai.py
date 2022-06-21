import asyncio
import logging
import os
from threading import Thread
import aiohttp
import aiofiles
from pycqBot.cqApi import cqBot, cqHttpApi
from pycqBot.object import Plugin, Message
from pycqBot.cqCode import node_list, image
from lxml import etree


class imhentai(Plugin):

    def __init__(self, bot: cqBot, cqapi: cqHttpApi, plugin_config) -> None:
        super().__init__(bot, cqapi, plugin_config)
        self._download_path = plugin_config["download_path"] if "download_path" in plugin_config else "./plugin/nhentai/download"
        self._limit = plugin_config["limit"] if "limit" in plugin_config else 10
        self._chunk_size = plugin_config["chunk_size"] if "chunk_size" in plugin_config else 1024
        self._forward_name = plugin_config["forward_name"]
        self._forward_qq = plugin_config["forward_qq"]
        self._reply_time = plugin_config["replyTime"] if "replyTime" in plugin_config else 60
        self._proxy = ("http://%s" % plugin_config["proxy"]) if "proxy" in plugin_config else None

        bot.command(self.select, "本子", {
            "type": "all"
        })

        bot.command(self.select_id, "imh", {
            "type": "all"
        })
    
    async def get_book(self, book_url):
        html = await self.cqapi.link(book_url, json=False, proxy=self._proxy)
        html = etree.HTML(html)

        page_url_list = []
        page = int(html.xpath('//li[@class="pages"]/text()')[0].strip("Pages: "))
        img_data_url = html.xpath('//*[@id="append_thumbs"]/div[1]/div/a/img/@data-src')[0].rsplit("/", maxsplit=1)[0]
        for page_in in range(1, page+1):
            page_url_list.append("%s/%s.jpg" % (img_data_url, page_in))
        
        return page_url_list
    
    async def _download_page(self, session, page_url, book_path):
        try:
            async with session.get(page_url, proxy=self._proxy) as req:
                file_name = page_url.rsplit("/", maxsplit=1)[-1]

                async with aiofiles.open("%s/%s" % (book_path, file_name), "wb") as file:
                    async for chunk in req.content.iter_chunked(self._chunk_size):
                        await file.write(chunk)
        except Exception as err:
            logging.warning("nhentai %s 下载 error: %s" % (page_url, err))
    
    async def download_book(self, book_url):
        try:
            book_id = book_url.rstrip("/").rsplit("/", maxsplit=1)[-1]
            book_path = "%s/%s" % (self._download_path, book_id)
            if os.path.isdir(book_path):
                return book_path

            page_url_list = await self.get_book(book_url)
            if page_url_list == []:
                return None

            book_path = os.path.join(self._download_path, "%s" % book_id)

            os.makedirs(book_path)
            conn = aiohttp.TCPConnector(limit=self._limit)
            async with aiohttp.ClientSession(connector=conn) as session:
                tasks = []
                for page_url in page_url_list:
                    tasks.append(asyncio.create_task(self._download_page(session, page_url, book_path)))
                
                await asyncio.wait(tasks)
            
            logging.debug("imhentai %s all page %s" % (book_id, len(page_url_list)))
            return book_path
        except Exception as err:
            logging.error("imhentai %s 下载 error: %s" % (page_url, err))
            logging.exception(err)

    async def _send_book(self, book_path, message):
        try:
            forward_message_list = []
            
            file_list = sorted(os.listdir(book_path), key=lambda i:int(i.split(".")[0]))
            if len(file_list) > 200:
                page = int(len(file_list) / 200)
                page_in = 0
                while page_in < page + 1:
                    message_list = []
                    max_in = page_in * 200 + 200
                    if max_in > len(file_list):
                        max_in = len(file_list)

                    for file in file_list[page_in * 200: max_in]:
                        file_path = os.path.abspath("%s/%s" % (book_path, file))
                        message_list.append(image("file://%s" % file_path))
                    
                    forward_message_list.append(message_list)
                    page_in += 1
            else:
                message_list = []
                for file in file_list:
                    file_path = os.path.abspath("%s/%s" % (book_path, file))
                    message_list.append(image("file://%s" % file_path))
                
                forward_message_list.append(message_list)

            print(forward_message_list)
            for message_list in forward_message_list:
                self.cqapi.send_group_forward_msg(message.group_id, node_list(message_list, 
                    self._forward_name,
                    self._forward_qq
                ))
        except Exception as err:
            logging.exception(err)
    
    async def send_book(self, message: Message, book_data_list, book_index):
        book_data = book_data_list[book_index]
        book_path = await self.download_book(book_data["url"])
        logging.info("nhentai %s 下载完成" % book_data["title"])
        await self._send_book(book_path, message)

    def send_select_list(self, select_list, message: Message):
        message_list = ['使用 "#本子 [搜索内容] [页数]" 翻页, 发送序号查看']
        for index, book_data in enumerate(select_list):
            if len(book_data["title"]) > 30:
                message_list.append("%s. %s" % (index, book_data["title"][0:30]))
            else:
                message_list.append("%s. %s" % (index, book_data["title"]))

            message_list.append("%s" % image("test.jpg", book_data["img"]))
            message_list.append(book_data["url"])

        self.cqapi.send_group_forward_msg(message.group_id, node_list(message_list, 
            self._forward_name,
            self._forward_qq
        ))
    
    async def select_book(self, key, page=None):
        if page is None:
            page = 1
            
        api = "https://imhentai.xxx/search/?key=%s&page=%s" % (key, page)
        html = await self.cqapi.link(api, json=False, proxy=self._proxy)
        html = etree.HTML(html)

        page = int(html.xpath('//ul[@class="pagination"]/li')[-2].xpath("./a/text()")[0])
        select_list, book_data_list = html.xpath('//div[@class="thumb"]'), []
        for book_data in select_list:
            book_data_list.append({
                "title": book_data.xpath('.//div[@class="caption"]/a/text()')[0],
                "img": book_data.xpath('.//div[@class="inner_thumb"]/a/img/@src')[0],
                "url": "https://imhentai.xxx%s" % book_data.xpath('.//div[@class="caption"]/a/@href')[0]
            })
        
        return page, book_data_list
    
    async def _select(self, commandData, message: Message):
        if len(commandData) == 2:
            page, book_data_list = await self.select_book(commandData[0], commandData[1])
        else:
            page, book_data_list = await self.select_book(commandData[0])

        message.reply("搜索 %s 共计 %s 页" % (commandData[0], page))
        self.send_select_list(book_data_list, message)

        def send_book(book_data_list, message):
            message_data = self.cqapi.reply(message.user_id, self._reply_time)
            if message_data is None:
                message.reply("等待 %s 选择本子超时..." % message.sender["nickname"])
                return
            
            book_index = int(message_data.text)
            self.cqapi.add_task(self.send_book(message, book_data_list, book_index))

        thread = Thread(target=send_book, args=(book_data_list, message,))
        thread.setDaemon(True)
        thread.start()
    
    async def _select_id(self, commandData, message: Message):
        book_path = await self.download_book("https://imhentai.xxx/gallery/%s/" % commandData[0])
        logging.info("nhentai %s 下载完成" % commandData[0])
        await self._send_book(book_path, message)
    
    def select(self, commandData, message: Message):
        self.cqapi.add_task(self._select(commandData, message))
    
    def select_id(self, commandData, message: Message):
        self.cqapi.add_task(self._select_id(commandData, message))