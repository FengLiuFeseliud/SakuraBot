import logging
import os
from pycqBot.cqApi import cqBot, cqHttpApi
from pycqBot.object import Plugin, Message
from lxml import etree
from threading import Thread
from pycqBot.cqCode import node_list, image
import aiohttp
import aiofiles
import asyncio
from zipfile import ZipFile


class nhentai(Plugin):
    """
    基于 nhentai 的本子搜索
    https://nhentai.net

    使用异步并发下载本子, 比 go-cqhttp 内置下载更快

    插件配置
    ---------------------------

    forward_qq: 转发使用的 qq 号
    forward_name: 转发使用的名字
    download_path: 本子下载目录 默认 ./plugin/nhentai/download
    limit: 下载并发数 默认 10
    chunk_size: 流下载大小 默认 1024 (1mb)
    proxy: 代理 ip 
    replyTime: 等待选择图时长 单位秒 默认 60
    notSelectImage: 无图查询 (更快) 默认 False 关
    """

    def __init__(self, bot: cqBot, cqapi: cqHttpApi, plugin_config) -> None:
        super().__init__(bot, cqapi, plugin_config)
        self._proxy = ("http://%s" % plugin_config["proxy"]) if "proxy" in plugin_config else None
        self._reply_time = plugin_config["replyTime"] if "replyTime" in plugin_config else 60
        self._forward_name = plugin_config["forward_name"]
        self._forward_qq = plugin_config["forward_qq"]
        self._download_path = plugin_config["download_path"] if "download_path" in plugin_config else "./plugin/nhentai/download"
        self._limit = plugin_config["limit"] if "limit" in plugin_config else 10
        self._chunk_size = plugin_config["chunk_size"] if "chunk_size" in plugin_config else 1024
        self._not_select_image = plugin_config["notSelectImage"] if "notSelectImage" in plugin_config else False
        
        bot.command(self.select, "本子", {
            "type": "all"
        })
    
    def get_language(self, tar_list):
        """
        本子语言

        存在 6346 日语
        存在 29963 中文
        存在 12227 英语
        """

        if "6346" in tar_list:
            return "日语"
        
        if "29963" in tar_list:
            return "中文"
        
        if "12227" in tar_list:
            return "英语"
        
        return "未知"

    async def get_book(self, q):
        try:
            api = "https://nhentai.net/search/?q=%s" % q
            html = await self.cqapi.link(api, json=False, proxy=self._proxy)
            html = etree.HTML(html)

            book_data_list = []
            div_list = html.xpath('//div[@class="gallery"]')
            for div in div_list:
                book_language = self.get_language(div.xpath('./@data-tags')[0])
                book_data_list.append({
                    "title": div.xpath('.//div[@class="caption"]/text()')[0],
                    "img": div.xpath('.//img[@class="lazyload"]/@data-src')[0],
                    "url": "https://nhentai.net%s" % div.xpath('./a/@href')[0],
                    "language": book_language
                })
            
            return book_data_list
        except Exception as err:
            logging.error("nhentai 查询错误 error: %s" % err)
            logging.exception(err)
        
        return []

    async def get_book_page(self, book_url):
        try:
            html = await self.cqapi.link(book_url, json=False, proxy=self._proxy)
            return etree.HTML(html).xpath('//div[@class="thumb-container"]//img[@class="lazyload"]/@data-src')
        except Exception as err:
            logging.exception(err)
    
    async def _download_page(self, session, page_url, book_path):
        try:
            async with session.get(page_url, proxy=self._proxy) as req:
                file_name = page_url.rsplit("/", maxsplit=1)[-1]

                async with aiofiles.open("%s/%s" % (book_path, file_name), "wb") as file:
                    async for chunk in req.content.iter_chunked(self._chunk_size):
                        await file.write(chunk)
        except Exception as err:
            logging.warning("nhentai %s 下载 error: %s" % (page_url, err))

    async def download_book(self, page_url_list, book_id):
        try:
            book_path = os.path.join(self._download_path, "%s" % book_id)

            os.makedirs(book_path)
            conn = aiohttp.TCPConnector(limit=self._limit)
            async with aiohttp.ClientSession(connector=conn) as session:
                tasks = []
                for page_url in page_url_list:
                    # 原图 url
                    page_url = page_url.replace("/t", "/i", 1).replace("t.", ".", 1)
                    tasks.append(asyncio.create_task(self._download_page(session, page_url, book_path)))
                
                await asyncio.wait(tasks)
            
            return book_path
        except Exception as err:
            logging.error("nhentai %s 下载 error: %s" % (page_url, err))
            logging.exception(err)
    
    async def _send_book(self, book_path, message):
        message_list = []
        
        for file in sorted(os.listdir(book_path), key=lambda i:int(i.split(".")[0])):
            file_path = os.path.abspath("%s/%s" % (book_path, file))
            message_list.append(image("file://%s" % file_path))

        self.cqapi.send_group_forward_msg(message.group_id, node_list(message_list, 
            self._forward_name,
            self._forward_qq
        ))


    async def send_book(self, message: Message, book_data_list, book_index):
        book_data = book_data_list[book_index]
        book_id = book_data["url"].rstrip("/").rsplit("/", maxsplit=1)[-1]
        book_path = "%s/%s" % (self._download_path, book_id)
        if os.path.isdir(book_path):
            logging.info("nhentai %s 已经存在直接发送" % book_data["title"])
            return await self._send_book(book_path, message)

        page_url_list = await self.get_book_page(book_data["url"])
        if page_url_list == []:
            return

        book_path = await self.download_book(page_url_list, book_id)
        logging.info("nhentai %s 下载完成" % book_data["title"])
        logging.debug("nhentai %s all page %s" % (book_data["title"], len(page_url_list)))

        await self._send_book(book_path, message)

    async def upload_book(self, message: Message, book_data_list, book_index):
        try:
            book_data = book_data_list[book_index]
            book_id = book_data["url"].rstrip("/").rsplit("/", maxsplit=1)[-1]
            book_path = "%s/%s.zip" % (self._download_path, book_id)
            if os.path.isfile(book_path):
                logging.info("nhentai %s 已经存在直接上传" % book_data["title"])
                return self.cqapi.upload_group_file(
                    message.group_id, 
                    os.path.abspath(book_path), 
                    "%s.zip" % book_id
                )

            book_path = await self.download_book(await self.get_book_page(book_data["url"]), book_id)
            logging.info("nhentai %s 下载完成, 准备上传" % book_data["title"])
            with ZipFile("%s.zip" % book_path, "w") as zip:
                print(os.listdir(book_path))
                for file in os.listdir(book_path):
                    file_path = "%s/%s" % (book_path, file)
                    zip.write(file_path)

                    os.remove(file_path)
            os.rmdir(book_path)

            self.cqapi.upload_group_file(
                message.group_id, 
                os.path.abspath(book_path), 
                "%s.zip" % book_id
            )
            return
        except Exception as err:
            logging.error("nhentai %s 上传 error: %s" % (book_data["title"], err))
            logging.exception(err)

    async def _select(self, commandData, message: Message):
        try:
            book_data_list = await self.get_book(commandData[0])

            logging.debug("nhentai %s 查询到 %s count" % (commandData[0], len(book_data_list)))
            if book_data_list == []:
                message.reply("没有查询到本子 %s " % commandData[0])
                return

            message_list = []
            for index, book_data in enumerate(book_data_list):
                img_name = book_data["img"].rsplit("/", maxsplit=1)[-1]
                if self._not_select_image:
                    message_list.append("%s.%s" % (index,
                        "%s\n语言：%s\n%s" % (
                            book_data["title"][:35],
                            book_data["language"],
                            book_data["url"]
                        )
                    ))
                else:
                    message_list.append("%s.%s" % (index,
                        "%s\n语言：%s\n%s\n%s" % (
                            book_data["title"][:35],
                            book_data["language"],
                            image(img_name, book_data["img"]),
                            book_data["url"]
                        )
                    ))
            
            self.cqapi.send_group_forward_msg(message.group_id, node_list(message_list, 
                self._forward_name,
                self._forward_qq
            ))

            def send_book(book_data_list, message):
                message.reply("等待 %s 选择本子，发送序号查看" % message.sender["nickname"])
                message_data = self.cqapi.reply(message.user_id, self._reply_time)
                if message_data is None:
                    message.reply("等待 %s 选择本子超时..." % message.sender["nickname"])
                    return
                
                book_index = int(message_data.text)
                
                message.reply('发送 "在线" 在线查看本子')
                message_data = self.cqapi.reply(message.user_id, self._reply_time)
                if message_data is None:
                    message.reply("等待 %s 选择本子查看模式超时..." % message.sender["nickname"])
                    return

                if message_data.text == "在线":
                    self.cqapi.add_task(self.send_book(message, book_data_list, book_index))
                
                if message_data.text == "下载":
                    """
                    go-cqhttp api 无法上传
                    """
                    # self.cqapi.add_task(self.upload_book(message, book_data_list, book_index))
                    message.reply('暂时 API 无法上传群文件')
            
            thread = Thread(target=send_book, args=(book_data_list, message,))
            thread.setDaemon(True)
            thread.start()

        except Exception as err:
            message.reply("发生错误！%s" % err)
            logging.error("nhentai _select error: %s" % err)
            logging.exception(err)

    def select(self, commandData, message: Message):
        self.cqapi.add_task(self._select(commandData, message))