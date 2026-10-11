# WePulse

WePulse 是一个自托管的微信公众号更新监测服务。用户提交任意一篇微信原文链接后，系统自动识别公众号、建立监测基线，随后定时采集新文章，并通过网页 API、RSS、Markdown 摘要或 Webhook 输出结果。

> 当前版本：0.3.4。Windows 用户无需 Docker，也无需预先安装 Python；双击启动脚本会自动准备运行环境。微信及微信读书相关网页接口不是稳定的开放内容 API，可能发生变更、登录过期或频率限制。请遵守适用的服务条款，不要进行高频、批量或商业化抓取。

## 1. 文档导航

| 文档 | 适合谁 | 内容 |
|---|---|---|
| [QUICKSTART.zh-CN.txt](QUICKSTART.zh-CN.txt) | 第一次使用的 Windows 用户 | 最短安装、启动和 Cookie 接入流程 |
| [README.md](README.md) | 所有用户 | 完整功能、部署、配置、API、备份和升级说明 |
| [CODEX_AUTOMATION.zh-CN.md](CODEX_AUTOMATION.zh-CN.md) | 使用 Codex 的用户 | 一键创建每日汇总与失败重试自动化的指令模板 |
| [TROUBLESHOOTING.zh-CN.md](TROUBLESHOOTING.zh-CN.md) | 启动或采集遇到问题的用户 | 乱码、权限、令牌、Cookie、400/401、端口和定时任务排查 |
| [OPEN_SOURCE_RELEASE.zh-CN.md](OPEN_SOURCE_RELEASE.zh-CN.md) | 准备发布源码的维护者 | 去除个人信息、凭据检查、打包和发布前验收清单 |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 贡献者 | 开发、测试和提交要求 |

## 2. 第一次使用：按这 6 步完成

1. **准备目录**：解压到 `D:\WePulse` 或 `F:\WePulse`，确认当前账户具有“修改”权限。
2. **启动服务**：双击 `start-wepulse.cmd`，首次运行保持联网并等待环境准备完成。
3. **登录管理中心**：在自动打开的网页中粘贴启动脚本复制的管理令牌。
4. **录入 Cookie**：从微信读书主域名请求复制完整 Cookie，在管理中心安全保存并检查。
5. **添加公众号**：粘贴任意一篇公开微信原文链接，点击“识别并添加”。
6. **检查结果**：点击“立即采集全部”，再打开“今日摘要”或“聚合 RSS”。

需要外部推送时，再配置企业微信、邮件或 Webhook；只想使用网页和 RSS 的用户可以跳过通知配置。

## 3. 使用前必读：两个必要条件

| 必要条件 | 为什么需要 | 用户要做什么 |
|---|---|---|
| 首次运行时可访问互联网、Windows 带有 WinGet，并且安装目录可写 | 脚本需要安装 uv，并在项目目录创建 `.env`、Python 环境和数据库 | 在 PowerShell 运行 `winget --version`；把项目解压到当前账户具有“修改”权限的目录，首次双击启动时保持联网 |
| 有效的微信读书 Web 登录 Cookie | 微信读书最新文章接口需要登录状态，WePulse 不会也不能代替用户登录 | 用户在浏览器登录微信读书，在本机管理中心安全录入 Cookie，然后验证 |

首次安装完成后，日常启动一般不需要重新下载。Cookie 会过期，过期后需要重新登录微信读书并更新；这是微信登录状态的正常安全机制。

### 3.1 条件一：检查网络与 WinGet

打开 PowerShell：

```powershell
winget --version
```

如果显示版本号，可以直接双击 `start-wepulse.cmd`。脚本会通过 WinGet 安装官方 uv，并把 Python、虚拟环境和缓存放在项目目录中。若提示找不到 WinGet，请先从 Microsoft Store 安装或更新“应用安装程序（App Installer）”，再重新运行。

首次安装过程中请勿关闭窗口。网络中断时不会破坏配置，恢复网络后重新双击即可继续。

项目目录必须允许当前 Windows 账户写入。右键项目文件夹，打开 **属性 → 安全**，当前账户至少应具有“修改”权限；只有“读取和执行”时无法创建 `.env`。不要为了绕过权限问题而长期以管理员身份运行 WePulse。

### 3.2 条件二：安全接入微信读书 Cookie

Cookie 相当于当前微信读书 Web 登录凭据。**不要把 Cookie 发给作者、聊天机器人、群聊、GitHub Issue，也不要放入截图或提交到 Git。** 管理中心会把它写入当前项目的 `.env`，但不会在保存后回显。

获取步骤（Chrome、Edge 等 Chromium 浏览器）：

1. 打开 `https://weread.qq.com/`，使用自己的账号扫码登录。
2. 按 `F12` 打开开发者工具，选择 **Network / 网络**。
3. 保持 Network 正在录制，刷新微信读书页面。
4. 选择任意发往主域名 `https://weread.qq.com/` 的请求；不要选择 `oss.weread.qq.com`。
5. 打开 **Headers / 标头 → Request Headers / 请求标头**。
6. 找到 `Cookie:`，只复制冒号后面的完整内容。
7. 打开 WePulse 管理中心，在“录入或更新微信读书 Cookie”中粘贴并点击“安全保存”。系统会检查 `wr_vid`、`wr_skey` 和不可见字符，保存后立即生效。
8. 点击“检查 Cookie”。显示“Cookie 验证成功”才算接入完成。

微信读书网页不一定提供公众号搜索入口，也不需要先在其中找到公众号。只要从主域名请求取得完整 Cookie，具体公众号由 WePulse 根据微信原文链接识别。Cookie 失效时重复以上步骤即可；无需删除订阅和历史文章。

## 4. 用自己的账号进行首次实验

建议先只添加一个公众号，按以下顺序验收：

1. 双击 `start-wepulse.cmd`，等待管理中心自动打开。
2. 在登录框粘贴剪贴板中的管理令牌并保存。
3. 按上面的步骤接入自己的微信读书 Cookie。
4. 粘贴一篇公开微信原文链接，确认系统识别出公众号名称和文章标题。
5. 点击“检查 Cookie”，确认验证成功。
6. 点击“立即采集全部”，确认订阅状态为“正常”。
7. 打开“今日摘要”和“聚合 RSS”，确认标题和原文链接可以访问。
8. 如需通知，再配置邮件或企业微信并点击“测试每日推送”。

实验过程中不要把 `.env`、`data/`、日志或 Cookie 发给他人。公开发布项目时只发布源码包。

## 5. 使用入口

服务启动后，普通用户主要使用下面三个入口：

| 入口 | 地址 | 用途 |
|---|---|---|
| **管理中心（推荐）** | `http://localhost:8765/admin` | 添加公众号、检查 Cookie、查看失败、手动采集和测试推送 |
| 接口文档 | `http://localhost:8765/docs` | 高级配置与 API 调试 |
| 聚合 RSS | `http://localhost:8765/feeds/all.xml` | 添加到 Feedly、FreshRSS、Miniflux 等阅读器 |

Windows 一键启动会把管理令牌复制到剪贴板。第一次打开管理中心时，在登录框中直接粘贴即可；令牌只保存在当前浏览器中。

## 6. 功能

- 从任意 `mp.weixin.qq.com` 原文链接自动识别公众号名称及唯一标识
- 微信读书最新文章采集器，以及通用 RSS 采集器
- SQLite 持久化、文章去重和监测基线
- 定时采集和每日 Markdown 汇总
- 中文网页管理中心和醒目的采集失败提示
- 网页安全录入、更新和真实状态检查 Cookie
- 每日邮件、企业微信机器人和通用 Webhook 推送
- 聚合 RSS、单公众号 RSS 和 JSON API
- 明确记录登录失效、采集异常和最后检查时间
- Windows 双击安装、后台启动、停止和开机自启动
- 首次运行自动通过 WinGet 安装 uv，并由 uv 自动准备 Python 3.12
- Docker 与本地 Python 两种运行方式

## 7. 工作方式

```text
公开原文链接 → 识别公众号 → 定时低频采集 → SQLite 去重
                                        ↓
                    RSS / JSON API / 每日摘要 / Webhook
```

默认每 60 分钟采集一次，并在 `Asia/Shanghai` 时区每天 06:00 生成过去 24 小时摘要。采集时间和汇总时间都可通过环境变量修改。

## 8. 修改每日推送时间

每日摘要时间由项目目录中的 `.env` 控制。目前管理网页会显示时间，但不能直接修改；Windows 用户可双击 `open-config.cmd` 打开配置。

### 8.1 操作步骤

1. 双击 `open-config.cmd`。
2. 找到以下三项：

   ```env
   TZ=Asia/Shanghai
   DIGEST_HOUR=6
   DIGEST_MINUTE=0
   ```

3. 修改小时和分钟并保存。
4. 双击 `restart-wepulse.cmd` 让新时间生效。
5. 打开管理中心，在“每日任务”处确认显示的新时间。

### 8.2 示例

每天北京时间 09:30 推送：

```env
TZ=Asia/Shanghai
DIGEST_HOUR=9
DIGEST_MINUTE=30
```

每天北京时间 18:00 推送：

```env
TZ=Asia/Shanghai
DIGEST_HOUR=18
DIGEST_MINUTE=0
```

### 8.3 取值和注意事项

- `DIGEST_HOUR`：`0`～`23`。
- `DIGEST_MINUTE`：`0`～`59`。
- `TZ=Asia/Shanghai` 表示北京时间；除非明确需要其他时区，否则不要修改。
- 修改 `.env` 后必须重启；只刷新网页不会重新加载定时配置。
- 该时间控制 WePulse 的邮件、企业微信和 Webhook 摘要，也控制本机生成 `latest_digest.md` 的时间。
- RSS 和网页文章列表不依赖每日推送时间，仍按采集间隔更新。
- Codex 聊天中的定时汇总是独立自动化，修改 `.env` 不会同步修改 Codex 的运行时间。
- 如果电脑在设定时间关机、服务未运行或没有网络，内置每日任务不会无限补发；可恢复后手动测试推送，或使用外部调度器进行失败重试。

### 8.4 修改普通采集间隔

每日推送时间与文章采集间隔是两项不同设置。修改采集间隔使用：

```env
COLLECT_INTERVAL_MINUTES=60
```

允许值最低为 15 分钟。建议保持 60～120 分钟，避免高频访问上游接口。

### 8.5 接入 Codex 定时汇总（可选）

使用 Codex 桌面端的用户，可以让 Codex 在每天指定时间检查本机 WePulse，并在失败时定时重试。Codex 自动化与 WePulse 自带的邮件、企业微信和 Webhook 推送相互独立。

操作步骤：

1. 先正常启动 WePulse，并确认管理中心能够“立即采集全部”。
2. 打开一个 Codex 聊天。
3. 打开 [CODEX_AUTOMATION.zh-CN.md](CODEX_AUTOMATION.zh-CN.md)。
4. 把模板中的项目路径、首次运行时间和重试间隔替换成自己的设置。
5. 将完整模板发送给 Codex，并允许它读取 WePulse 项目及写入一个持久状态文件。
6. 检查 Codex 创建的自动化名称、时间和时区是否正确。

不要在指令中填写 Cookie、`ADMIN_TOKEN`、邮箱密码或 Webhook。模板要求 Codex仅在本机安全读取所需令牌，并禁止在消息或日志中输出凭据。

## 9. 安装与启动

根据操作系统和使用习惯选择下面一种方式即可。普通 Windows 用户优先选择方法一；已经安装 Docker 的用户可以选择方法二。方法三和方法四主要面向需要自行维护运行环境的用户或开发者。

### 9.1 方法一：Windows 本地一键启动（推荐）

要求：Windows 10/11、网络连接，以及系统自带的 WinGet。不需要 Docker、WSL，也不需要预先安装 Python。

Windows 用户解压项目后，直接双击：

```text
start-wepulse.cmd
```

首次运行会自动完成以下工作：

1. 通过 WinGet 安装轻量级环境管理器 uv。
2. 在项目目录中准备 Python 3.12 和依赖，不污染系统 Python。
3. 创建 `.env` 并生成随机管理令牌。
4. 在后台启动 WePulse、复制管理令牌并打开管理中心。
5. 用户可在管理中心安全录入微信读书 Cookie。

以后再次双击同一个文件即可启动或打开管理中心，不会覆盖配置和数据。

`start-wepulse.cmd` 启动成功后，WePulse 使用隐藏的后台进程运行；显示“已在后台运行”后，启动用的命令窗口和管理网页都可以关闭。关闭网页不会停止采集。需要停止服务时必须双击 `stop-wepulse.cmd`，不要直接在任务管理器中随意结束不确定的 Python 进程。

停止后台服务，双击：

```text
stop-wepulse.cmd
```

Cookie 直接在管理中心录入并立即生效；邮件、Webhook 等高级配置仍可通过 `open-config.cmd` 修改，随后双击 `restart-wepulse.cmd`。项目根目录还提供纯文本快速指南 `QUICKSTART.zh-CN.txt`。

双击 `restart-wepulse.cmd` 后自动重新打开管理网页是正常行为，表示脚本已经先停止旧进程再启动新进程。网页本身不是后台服务，关掉它不影响 WePulse。

需要登录 Windows 后自动运行时，先完成一次启动，再双击：

```text
install-autostart.cmd
```

取消开机自启动，双击：

```text
remove-autostart.cmd
```

本地数据、运行日志和 PID 文件均保存在项目的 `data/` 目录。建议将整个项目解压到长期不移动的位置，例如 `D:\WePulse` 或 `F:\WePulse`。

### 9.2 方法二：Docker 一键启动（可选）

需要先安装并启动 Docker Desktop 或 Docker Engine。Windows 用户双击：

```text
start-docker.cmd
```

Linux 或 macOS：

```bash
chmod +x start.sh
./start.sh
```

停止 Docker 服务：

```bash
docker compose down
```

这不会删除 `data/` 中的订阅和历史记录。

### 9.3 方法三：手工 Docker 部署

需要 Docker Desktop、Docker Engine 或兼容的 Compose 环境。

```bash
git clone <YOUR_REPOSITORY_URL> wepulse
cd wepulse
cp .env.example .env
docker compose up -d --build
```

Windows PowerShell 可使用：

```powershell
Copy-Item .env.example .env
docker compose up -d --build
```

启动后访问：

- 管理中心：`http://localhost:8765/admin`
- 健康检查：`http://localhost:8765/health`
- 交互式接口文档：`http://localhost:8765/docs`
- 聚合 RSS：`http://localhost:8765/feeds/all.xml`

### 9.4 方法四：手工本地运行

适合开发者。安装 [uv](https://docs.astral.sh/uv/) 后执行：

```powershell
Copy-Item .env.example .env
uv sync --locked
uv run python -m wepulse
```

Linux 或 macOS 手工运行：

```bash
cp .env.example .env
uv sync --locked
uv run python -m wepulse
```

## 10. 管理中心使用方法

1. 打开 `http://localhost:8765/admin`。
2. 从 `.env` 复制 `ADMIN_TOKEN`，在“登录”区域保存。
3. 将任意一篇 `https://mp.weixin.qq.com/s/...` 原文粘贴到“通过微信原文添加公众号”。
4. 点击“检查 Cookie”，确认显示“Cookie 验证成功”。
5. 点击“立即采集全部”可以立刻检查；系统也会按配置自动运行。
6. 在“订阅与失败提示”查看最后检查时间和具体错误；错误消失表示下一次采集已经恢复。
7. 配置邮件或企业微信后，点击“测试每日推送”验证渠道。

### 10.1 管理中心按钮分别做什么

| 按钮 | 实际动作 | 正常结果 |
|---|---|---|
| 保存并刷新 | 只保存当前浏览器中的管理令牌并重新读取状态 | 页面出现订阅、Cookie 和定时任务状态 |
| 刷新页面 | 重新加载当前页面和状态，不会触发采集 | 数据未变化也是正常现象 |
| 立即采集全部 | 立刻检查所有已启用订阅 | 页面提示新增篇数，失败会出现在订阅列表 |
| 检查 Cookie | 使用第一个微信读书订阅进行一次真实验证 | 显示“验证成功”；没有订阅时只能确认已配置 |
| 测试每日推送 | 把当前 24 小时摘要发送到已经配置的通知渠道 | 未配置邮件、企业微信或 Webhook 时不会产生外部消息 |

如果按钮看起来“没有反应”，先查看页面顶部或按钮附近的提示，再检查 `data/service.err.log`。浏览器强制刷新可使用 `Ctrl+F5`，但刷新不会代替采集。

删除订阅会同时删除它的历史文章且不可撤销，管理中心会在操作前再次确认。

## 11. 首次配置

### 11.1 设置管理令牌

编辑 `.env`，将：

```env
ADMIN_TOKEN=change-me
```

替换为随机长字符串。PowerShell 可以生成一个随机值：

```powershell
[guid]::NewGuid().ToString('N')
```

所有写操作都需要请求头：

```text
Authorization: Bearer <ADMIN_TOKEN>
```

不要把 `.env` 提交到 Git。项目已经通过 `.gitignore` 和 `.dockerignore` 排除它。

### 11.2 配置微信读书登录

监测任意公众号需要用户自己的微信读书 Web 登录状态：

1. 浏览器打开 `https://weread.qq.com/` 并扫码登录。
2. 按 `F12` 打开开发者工具，选择 **Network / 网络**。
3. 刷新页面，选择任意发往主域名 `https://weread.qq.com/` 的请求，不要选择 `oss.weread.qq.com`。
4. 在 **Request Headers / 请求标头** 中复制完整的 `Cookie` 值。
5. 在本机管理中心的“录入或更新微信读书 Cookie”区域粘贴并点击“安全保存”。保存后立即生效，无需重启。

然后进入管理中心点击“检查 Cookie”。检查会使用第一个微信读书订阅执行一次真实请求：显示“验证成功”才表示当前登录状态可以采集。Cookie 过期后，管理首页会显示“可能已失效”，对应公众号也会保留具体错误。

## 12. 每日通知

每天北京时间 06:00，WePulse 会先采集全部订阅，再生成过去 24 小时摘要，然后发送到已配置的渠道。摘要中同时包含公众号名称、文章标题、原文链接和采集失败提示。

服务必须在 06:00 时处于运行状态，电脑也必须能够联网。当前内置定时器不会为错过的每日推送无限补发；恢复网络后，普通采集会按 `COLLECT_INTERVAL_MINUTES` 继续，但当日摘要需要在管理中心手动测试推送，或由外部任务调度器实现“每 30 分钟重试直到成功”。若使用 Codex、Windows 任务计划程序或其他调度器做补偿重试，应以“全部订阅无错误且通知渠道返回成功”为完成条件，避免把采集失败记录成成功。

### 12.1 企业微信机器人

在企业微信群中添加“群机器人”，复制 Webhook 地址并写入：

```env
WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=...
```

### 12.2 邮件

填写 SMTP 信息。例如使用启用 STARTTLS 的邮箱服务：

```env
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your-account@example.com
SMTP_PASSWORD=邮箱提供的应用专用密码
SMTP_USE_TLS=true
EMAIL_FROM=your-account@example.com
EMAIL_TO=receiver@example.com
```

多个收件人暂不支持；`SMTP_PASSWORD` 应使用邮箱服务商提供的应用专用密码，而不是公开在代码中。修改 `.env` 后重启服务，再到管理中心点击“测试每日推送”。

### 12.3 通用 Webhook

设置 `DIGEST_WEBHOOK_URL` 后，系统发送如下 JSON：

```json
{"text":"Markdown 摘要","format":"markdown"}
```

Cookie 等同于登录凭据：不要发到聊天、Issue、日志或代码仓库。若已泄露，请立即退出微信读书登录并重新登录。

## 13. 添加公众号

### 13.1 推荐：从微信原文链接自动添加

普通用户直接打开管理中心，在“通过微信原文添加公众号”中粘贴任意一篇公开原文：

```text
https://mp.weixin.qq.com/s/ARTICLE_ID
```

点击“识别并添加”后，系统会读取公开元数据、解析公众号唯一 ID、创建订阅，并把该文章保存为初始基线。添加完成后点击“检查 Cookie”和“立即采集全部”进行验证。微信读书网页本身不需要、也不一定能够搜索公众号。

开发者也可以打开 `http://localhost:8765/docs`，找到：

```text
POST /api/accounts/from-article
```

点击 **Try it out**，填入：

```json
{
  "url": "https://mp.weixin.qq.com/s/ARTICLE_ID"
}
```

先点击页面右上角的 **Authorize**，再填写授权值：

```text
Bearer <ADMIN_TOKEN>
```

系统会自动读取公开元数据、解析公众号唯一 ID、创建订阅，并把该文章保存为初始基线。

也可以使用命令行：

```bash
curl -X POST http://localhost:8765/api/accounts/from-article \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://mp.weixin.qq.com/s/ARTICLE_ID"}'
```

### 13.2 RSS 来源

```bash
curl -X POST http://localhost:8765/api/accounts \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"示例来源","connector":"rss","feed_url":"https://example.com/feed.xml"}'
```

### 13.3 手工导入文章

```bash
curl -X POST http://localhost:8765/api/import \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"account_name":"示例公众号","url":"https://mp.weixin.qq.com/s/ARTICLE_ID","title":"文章标题"}'
```

## 14. 配置项

| 环境变量 | 默认值 | 作用 |
|---|---:|---|
| `APP_NAME` | `WePulse` | 服务名称 |
| `HOST` | `0.0.0.0` | 监听地址 |
| `PORT` | `8765` | 服务端口 |
| `DATA_DIR` | `data` | SQLite 和摘要目录 |
| `ADMIN_TOKEN` | `change-me` | 管理写操作令牌，必须修改 |
| `TZ` | `Asia/Shanghai` | 定时任务时区 |
| `COLLECT_INTERVAL_MINUTES` | `60` | 采集间隔，最低强制为 15 分钟 |
| `DIGEST_HOUR` | `6` | 每日摘要小时 |
| `DIGEST_MINUTE` | `0` | 每日摘要分钟 |
| `DIGEST_WEBHOOK_URL` | 空 | 可选摘要 Webhook |
| `WECOM_WEBHOOK_URL` | 空 | 企业微信群机器人 Webhook |
| `SMTP_HOST` | 空 | 邮件服务器；留空表示不发邮件 |
| `SMTP_PORT` | `587` | SMTP 端口 |
| `SMTP_USERNAME` | 空 | SMTP 用户名 |
| `SMTP_PASSWORD` | 空 | SMTP 应用专用密码 |
| `SMTP_USE_TLS` | `true` | 是否启用 STARTTLS |
| `EMAIL_FROM` | 空 | 发件地址，留空时使用 SMTP 用户名 |
| `EMAIL_TO` | 空 | 每日摘要收件地址 |
| `WEREAD_COOKIE` | 空 | 微信读书登录 Cookie |
| `WEREAD_CONTENT` | `false` | 是否额外获取正文 |
| `REQUEST_TIMEOUT_SECONDS` | `20` | 外部请求超时 |

## 15. API 与 RSS

- `GET /health`：服务和数据库状态
- `GET /admin`：网页管理中心
- `GET /api/status`：Cookie、任务、通知和错误概况
- `GET /api/accounts`：订阅列表及最后一次错误
- `POST /api/accounts/from-article`：从微信原文自动添加
- `POST /api/accounts`：手工添加 RSS 或微信读书订阅
- `POST /api/accounts/{id}/collect`：立即采集单个来源
- `POST /api/collect`：立即采集全部来源
- `POST /api/checks/weread`：使用真实订阅验证 Cookie
- `PUT /api/config/weread-cookie`：安全保存 Cookie 并立即应用，不回显凭据
- `POST /api/notifications/test`：测试已配置的推送渠道
- `DELETE /api/accounts/{id}`：删除订阅及其历史文章
- `GET /api/articles?hours=24`：最近文章
- `GET /api/digest?hours=24`：Markdown 摘要
- `GET /feeds/all.xml`：全部订阅 RSS
- `GET /feeds/{account_id}.xml`：单一订阅 RSS

## 16. 数据、备份和升级

默认数据位于 `data/`：

- `wepulse.db`：订阅、文章和状态
- `latest_digest.md`：最近一次每日摘要
- `last_notification.json`：上一次推送时间及各渠道结果（不包含密码）
- `service.out.log`、`service.err.log`：Windows 本地后台运行日志
- `wepulse.pid`：Windows 本地后台进程记录

升级前停止服务并备份整个 `data/` 目录。Windows 本地版可先双击 `stop-wepulse.cmd`；升级源码后再次双击 `start-wepulse.cmd`，脚本会根据锁文件自动同步依赖。Docker 用户必须保留 Compose 中的数据卷映射，否则重建容器时数据会丢失。

```bash
docker compose down
docker compose pull
docker compose up -d --build
```

## 17. 测试

```bash
uv sync --extra dev
uv run pytest -q
```

## 18. 常见问题

更完整、按症状分类的处理步骤见 [TROUBLESHOOTING.zh-CN.md](TROUBLESHOOTING.zh-CN.md)。下面只保留最常见情况。

### 18.1 返回 `401 LOGIN ERR`

`WEREAD_COOKIE` 缺失或过期。重新登录微信读书，从浏览器主域名请求中复制新 Cookie，在管理中心安全保存后重新检查。

### 18.2 管理中心提示 401 或 503

- `401`：浏览器里保存的令牌与 `.env` 中的 `ADMIN_TOKEN` 不一致，重新复制并保存。
- `503`：仍在使用默认的 `ADMIN_TOKEN=change-me`。请改为随机长字符串并重启服务。

如果刚移动、升级过项目，401 还可能表示旧目录中的 WePulse 仍占用 `8765` 端口。先从旧目录运行 `stop-wepulse.cmd`，再从当前目录运行 `start-wepulse.cmd`，然后把新复制到剪贴板的令牌重新粘贴到管理中心。不要把令牌发给任何人。

### 18.3 微信读书接口返回 400

先在管理中心重新保存完整 Cookie 并点击“检查 Cookie”。获取 Cookie 时必须选择主机名**恰好为** `weread.qq.com` 的请求；`https://oss.weread.qq.com/river/batch` 属于静态资源/批处理子域名，不应作为 Cookie 来源。如果所有订阅同时失败，通常是 Cookie、登录状态或上游接口变化；如果只有单个订阅失败，可用该公众号最新的公开原文链接重新添加验证。

### 18.4 PowerShell 出现乱码并提示“字符串缺少终止符”

这通常不是命令写错，而是 `.ps1` 文件被旧版 Windows PowerShell 用错误编码读取。请重新下载当前发布包，不要用会改变编码的工具保存启动脚本；当前发布包的 PowerShell 文件应使用兼容 Windows PowerShell 5 的 UTF-8 BOM。详细恢复步骤见故障排查文档。

### 18.5 创建 `.env` 时提示“访问被拒绝”

当前账户没有项目目录的修改权限。优先把项目解压到自己拥有的 `D:\WePulse` 或 `F:\WePulse`，或者在文件夹“属性 → 安全 → 编辑”中为当前账户授予“修改”权限。不要通过长期使用管理员身份运行来掩盖权限配置问题。

### 18.6 测试推送失败

管理中心会显示各渠道返回结果。邮件失败时检查 SMTP 主机、端口、STARTTLS 和应用专用密码；企业微信失败时重新复制群机器人的完整 Webhook。修改 `.env` 后必须重启服务。

Windows 本地版依次双击：

```text
stop-wepulse.cmd
start-wepulse.cmd
```

Docker 版执行：

```bash
docker compose restart
```

### 18.7 双击启动后页面打不开

查看 `data/service.err.log`。常见原因是端口 `8765` 已被其他软件占用，或者首次下载 Python/依赖时网络中断。网络恢复后重新双击 `start-wepulse.cmd` 即可继续安装。若服务已经启动，脚本不会重复创建进程。

### 18.8 开机自启动没有运行

打开 Windows“任务计划程序”，检查名为 `WePulse` 的任务。该任务在当前用户登录后启动，因此电脑必须开机并完成用户登录，06:00 定时摘要才能执行。项目目录不能在安装任务后移动；如果已经移动，请先运行 `remove-autostart.cmd`，再在新目录运行 `install-autostart.cmd`。

### 18.9 订阅成功但没有新文章

- 先调用 `POST /api/accounts/{id}/collect`，再查看订阅的 `last_error`。
- 微信读书的最新文章接口通常只返回最近一篇，应保持每 1～2 小时低频采集。
- 如果一天只运行一次，公众号在两次运行之间连续发布时可能漏报。

### 18.10 为什么不直接使用微信公众号官方 API

官方接口主要服务于已授权、由调用者管理的公众号，不提供读取任意第三方公众号文章列表的通用公共接口。因此本项目将采集层隔离为适配器，以便接口变化时替换，而不影响数据库、摘要、RSS 和 API。

### 18.11 可以公开部署到互联网吗

不建议直接暴露。至少应使用强 `ADMIN_TOKEN`、HTTPS、反向代理和防火墙，并限制访问来源。绝不能公开 `.env`、Cookie、数据库或日志。

## 19. 项目结构

```text
src/wepulse/
  api.py                 HTTP API
  article_url.py         微信原文识别
  config.py              环境配置
  db.py                  SQLite 存储
  digest.py              摘要生成与推送
  scheduler.py           定时任务
  service.py             采集编排
  collectors/            可替换采集器
tests/                    核心测试
start-wepulse.cmd         Windows 本地一键启动
stop-wepulse.cmd          Windows 本地停止
restart-wepulse.cmd       Windows 本地重启
open-config.cmd           用记事本打开配置
install-autostart.cmd     安装登录自启动任务
remove-autostart.cmd      移除登录自启动任务
start-docker.cmd          Windows Docker 启动（可选）
```

## 20. 贡献

请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。安全问题请按 [SECURITY.md](SECURITY.md) 私下报告，不要在公开 Issue 中提交 Cookie、令牌或数据库。

### 20.1 联系方式

- 维护联系邮箱：<577493620@qq.com>
- 功能建议、使用反馈和普通问题优先通过 GitHub Issue 提交，便于公开跟踪和后续维护。
- 涉及安全漏洞或不适合公开讨论的问题，可以发送邮件并注明 WePulse 版本、操作系统和复现步骤。
- 无论通过 Issue 还是邮件联系，都不要发送 Cookie、`ADMIN_TOKEN`、`.env`、数据库、邮箱密码或包含个人信息的日志。

## 21. License

[MIT](LICENSE)
