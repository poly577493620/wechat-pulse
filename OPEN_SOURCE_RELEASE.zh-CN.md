# WePulse 开源发布检查清单

本页面向维护者，用于生成不包含个人信息和本机运行数据的公开源码包。

## 绝不能发布的内容

- `.env` 及任何真实 `ADMIN_TOKEN`、`WEREAD_COOKIE`；
- `data/`、SQLite 数据库、PID、摘要、通知记录和运行日志；
- `.venv/`、`.python/`、`.uv-cache/` 等本机运行环境；
- 邮件密码、企业微信或通用 Webhook 地址；
- 浏览器开发者工具截图中的 Cookie、Authorization 或个人账号；
- 含用户姓名、Windows 用户目录、私人仓库地址的调试文件。

仓库已经在 `.gitignore` 和 `.dockerignore` 中排除了主要敏感目录，但忽略规则不能替代发布前检查。曾经提交过的秘密即使后来删除，仍可能存在于 Git 历史中，必须立即轮换凭据并清理历史。

## 建议公开的内容

```text
.github/
src/
tests/
.env.example
.gitignore
.dockerignore
Dockerfile
docker-compose.yml
pyproject.toml
uv.lock
README.md
QUICKSTART.zh-CN.txt
TROUBLESHOOTING.zh-CN.md
CONTRIBUTING.md
SECURITY.md
CHANGELOG.md
LICENSE
Windows / Linux 启停脚本
```

`.env.example` 只能包含占位值，不应包含可用账号或 Cookie。

## 发布前验收

1. 从干净目录检查源码包，而不是直接压缩正在运行的项目目录。
2. 确认源码包内不存在 `.env`、`data/`、虚拟环境和缓存。
3. 全文搜索 `ADMIN_TOKEN=`、`WEREAD_COOKIE=`、`wr_vid=`、`wr_skey=`、`SMTP_PASSWORD=` 和 Webhook 域名，确认只有文档占位符。
4. 在 Windows PowerShell 5 中验证所有 `.ps1` 文件可以解析，避免 UTF-8 编码导致中文乱码和引号损坏。
5. 在一台没有预装 Python、Docker 的普通 Windows 环境执行一次 `start-wepulse.cmd`。
6. 验证首次启动能创建 `.env`、生成随机令牌、复制到剪贴板并打开管理中心。
7. 使用测试账号验证 Cookie 保存、真实检查、添加公众号、立即采集、摘要和 RSS。
8. 运行测试：`uv sync --extra dev`，然后 `uv run pytest -q`。
9. 确认 README 中版本号、更新日志、仓库地址和 Release 文件名一致。
10. 在 GitHub Release 中同时提供源码、校验值和升级说明；不要上传个人运行目录的压缩包。

## 推荐打包方式

如果项目已经纳入 Git，优先从已提交内容生成归档：

```bash
git archive --format=zip --output=WePulse-source.zip HEAD
```

如果尚未使用 Git，请新建一个空目录，只复制“建议公开的内容”，再进行上面的敏感信息检查。不要通过删除正在使用目录中的 `.env` 和 `data/` 来打包，以免误删个人配置和历史数据。

## 给最终用户写清楚的边界

- WePulse 是自托管监测工具，不是微信或微信读书官方服务；
- 用户必须使用自己的合法登录状态，并自行保管 Cookie；
- 微信读书网页接口可能变化、限流或失效；
- 项目不承诺绕过访问控制，也不应高频、批量或商业化抓取；
- Windows 本地版不依赖 Docker/WSL，但首次安装需要网络、WinGet 和可写目录；
- 06:00 每日任务需要电脑、服务和网络处于可用状态，补偿重试需要外部调度器。

## 发布后维护

- 在 Issue 模板中提醒用户不要粘贴 Cookie、令牌、数据库和未脱敏日志；
- 上游接口变化时先记录受影响版本和安全降级方式；
- 修改启动脚本时同时测试 Windows PowerShell 5 与 PowerShell 7；
- 修改配置项、入口地址或首次安装流程时，同步更新 README、快速指南和故障排查；
- 每次发布在 CHANGELOG 中列出用户可感知的变化及升级注意事项。
