# sakuraBot

基于 go-cqhttp pycqBot

pycqBot: [pycqBot](https://github.com/FengLiuFeseliud/pycqBot)

## 使用

```bash
git clone https://github.com/FengLiuFeseliud/SakuraBot
cd ./SakuraBot
# 下载 go-cqhttp 找自己版本
wget https://github.com/Mrs4s/go-cqhttp/releases/download/v1.0.0-rc1/go-cqhttp_linux_amd64.tar.gz
tar -zxcf go-cqhttp_linux_amd64.tar.gz
pip install pycqBot
python ./main.py
# 二维码登录...
```

## 插件配置

插件配置文件为 bot 根下的 plugin_config.yml

**_plugin_config.yml**

```yaml
# 通用
defaults: &defaults
    # 代理
    proxy: # clash proxy 127.0.0.1:7890
    # 转发使用的 qq 号
    forward_qq: # qq 号

# pycqBot.plugin.pixiv
pixiv: 
    # 转发使用的名字
    forward_name: "涩图"
    cookie: # pixiv cookie
    max_pid_len: 60
    <<: *defaults

# pycqBot.plugin.bilibili
bilibili:
    # 监听直播 uid 列表
    monitorLive:
        - 233114659
        - 205889201
    # 监听动态 uid 列表
    monitorDynamic:
        - 233114659
        - 205889201

# pycqBot.plugin.twitter
twitter:
    # 监听推文的用户名列表
    monitor: 
        - "azurlane_staff"
    # 需要在 twitter 申请 https://developer.twitter.com/
    bearerToken:  # twitter bearerToken
    <<: *defaults

# plugin/sukebei
sukebei:
    # 转发使用的名字
    forward_name: "磁力链接"
    maxLen: 5
    <<: *defaults

# plugin/saucenao
saucenao: 
    <<: *defaults

# plugin/blhx
blhx: 
    # 转发使用的名字
    forward_name: "wiki"
    <<: *defaults
```

## 插件

blhx: 碧蓝航线 wiki

sauceNAO: 基于 sauceNAO 的 pid 搜索

sukebei: 基于 sukebei 的磁力链接搜索

## 使用的 pycqBot 内置 插件

pycqBot.plugin.test: 测试插件

pycqBot.plugin.manage: 群管理插件 屏蔽词列表/群邀请处理/

pycqBot.plugin.bilibili: 实现 bilibili 监听动态/直播 消息 自动解析 bilibili qq 小程序分享信息

pycqBot.plugin.pixiv: 实现 pixiv 搜图/搜pid/搜用户图

pycqBot.plugin.twitter: 实现 twitter 监听推文

pycqBot.plugin.weather: 实现天气查询

## 自动处理

bilibili 监听动态/直播 消息

解析 bilibili qq 小程序分享信息

twitter 监听推文

## 可用指令

> ### pycqBot.plugin.weather
>
> **`#天气 [城市]`** 查询指定城市天气
>
> ### pycqBot.plugin.pixiv
>
> **`#搜索用户 [用户名] [指定量] [模式(可选)]`** pixiv 从指定用户返回指定量图 最后加上模糊 将使用模糊搜索
>
> **`#搜索作品 [用户名] [标签]`** pixiv 从指定标签返回指定量图
>
> **`#图来`** 从本 bot pixiv 用户 关注画师返回随机5张图
>
> **`#pid [pid]`** pixiv 从指定 pid 返回图
>
> ### sauceNAO
>
> **`#原图`** 基于 sauceNAO 的 pid 搜索
>
> ### sukebei
>
> **`#磁链 [标签]`** 基于 sukebei 的磁力链接搜索
>
> ### blhx
>
> **`#舰船筛选 [类型] ...`** 全舰船筛选 多个选项空格隔开
>
> **`#舰船 [舰船]`** 舰船查询
>
> ### pycqBot.plugin.manage
>
> **`#群邀请`** 手动处理群邀请
>
> **`#群邀请清空`** 群邀请清空
>
> ### pycqBot.plugin.test
>
> **`#echo [文本]`** 输出文本
>
> **`#code [cqCode] ...`** 输出 cqCode 数据
>
> **`#codestr [cqCode] ... `** 输出 cqCode 字符串