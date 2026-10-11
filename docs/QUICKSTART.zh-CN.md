WePulse Windows 快速开始
========================

一、运行条件
------------

1. Windows 10/11，并且首次运行时可以联网。
2. 系统带有 WinGet；可在 PowerShell 运行 winget --version 检查。
3. 项目文件夹允许当前账户“修改/写入”。
4. 监测微信公众号需要用户自己的微信读书 Web Cookie。

不需要安装 Docker、WSL，也不需要预先安装 Python。

二、首次启动
------------

1. 把整个文件夹解压到长期不移动的位置，例如 D:\WePulse 或 F:\WePulse。
2. 右键文件夹 → 属性 → 安全，确认当前账户具有“修改”权限。
3. 双击 start-wepulse.cmd。
4. 等待脚本安装 uv、准备 Python 3.12、创建配置并启动后台服务。
5. 管理令牌会复制到剪贴板；在自动打开的管理中心登录框中按 Ctrl+V。

看到“WePulse 已在后台运行”后，命令窗口和浏览器页面都可以关闭；关闭它们不会停止后台采集。需要结束服务时请双击 stop-wepulse.cmd。

三、接入 Cookie
--------------

Cookie 等同登录凭据，只能通过本机管理中心安全录入。不要发送到聊天、群聊、Issue、截图或 Git 仓库。

1. 浏览器登录 https://weread.qq.com/。
2. 按 F12 打开 Network / 网络，然后刷新页面。
3. 选择主机名恰好为 weread.qq.com 的请求，不要选择 oss.weread.qq.com。
4. 在 Request Headers / 请求标头中复制 Cookie 冒号后的完整内容。
5. 在管理中心“录入或更新微信读书 Cookie”中粘贴并点击“安全保存”。
6. 点击“检查 Cookie”，看到验证成功后再继续。

四、添加公众号并采集
------------------

1. 在管理中心粘贴任意一篇公开微信原文链接。
2. 点击“识别并添加”。
3. 点击“立即采集全部”。
4. 检查订阅状态、今日摘要和聚合 RSS。

“刷新页面”只重新读取状态，不会触发采集。

五、修改每日推送时间
------------------

1. 双击 `scripts\windows\open-config.cmd`。
2. 修改 .env 中的时间，例如每天北京时间 09:30：

   TZ=Asia/Shanghai
   DIGEST_HOUR=9
   DIGEST_MINUTE=30

3. 保存后双击 restart-wepulse.cmd。
4. 在管理中心“每日任务”处确认显示 09:30。

DIGEST_HOUR 可填写 0～23，DIGEST_MINUTE 可填写 0～59。
这个时间控制邮件、企业微信、Webhook 和本机每日摘要；不会自动修改 Codex 聊天的定时任务。

六、接入 Codex 定时汇总（可选）
----------------------------

如果使用 Codex 桌面端，请打开 [CODEX_AUTOMATION.zh-CN.md](CODEX_AUTOMATION.zh-CN.md)，替换项目路径、首次运行时间和重试间隔，再把完整模板发送给 Codex。

不要把 Cookie、ADMIN_TOKEN、邮箱密码或 Webhook 粘贴到聊天中。Codex 模板会要求自动化只在本机安全读取所需配置，并通过状态文件避免重复发送。

七、配置外部通知（可选）
----------------------

只有需要主动接收消息时才配置：

- 企业微信：WECOM_WEBHOOK_URL
- 邮件：SMTP_HOST、SMTP_USERNAME、SMTP_PASSWORD、EMAIL_TO 等
- 通用 Webhook：DIGEST_WEBHOOK_URL

修改后重启服务，再点击“测试每日推送”。未配置通知渠道时，点击测试不会产生外部消息。

八、常用入口
------------

- 启动或打开管理中心：`start-wepulse.cmd`
- 停止后台服务：`stop-wepulse.cmd`
- 重启服务：`restart-wepulse.cmd`
- 修改时间和通知配置：`scripts\windows\open-config.cmd`
- 安装登录自启动：`scripts\windows\install-autostart.cmd`
- 取消登录自启动：`scripts\windows\remove-autostart.cmd`
- 管理中心：http://localhost:8765/admin

restart 完成后自动打开网页是正常现象。

九、需要帮助时
--------------

- 完整说明：[README.md](../README.md)
- Codex 定时汇总模板：[CODEX_AUTOMATION.zh-CN.md](CODEX_AUTOMATION.zh-CN.md)
- 乱码、权限、401、Cookie 400 和定时任务：[TROUBLESHOOTING.zh-CN.md](TROUBLESHOOTING.zh-CN.md)
- 开源发布和脱敏检查：[OPEN_SOURCE_RELEASE.zh-CN.md](maintainers/OPEN_SOURCE_RELEASE.zh-CN.md)

禁止把 .env、data、Cookie、管理令牌、数据库和日志打包上传。
