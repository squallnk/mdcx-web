# MDCx Web

把 [MDCx](https://github.com/srz2/MDCx)（番号刮削器）改造成 Web 服务：在浏览器里开始/停止刮削、看实时日志与进度、读写配置、浏览并整理输出目录，打包成 Unraid 可直接拉取的 Docker 镜像。

上游本身就带了一套 FastAPI 服务端和一个 React 前端，本项目的工作是**让它真正跑得起来**、补齐缺失的停止能力、重做视觉，并打包成可部署形态——而不是从零重写。

## 结构

| 路径 | 作用 |
|---|---|
| `app/mdcx/` | 刮削引擎（上游源码 + 服务端可达性修复） |
| `app/resources/` | 番号正则表、字体、图片模板、映射表（运行时必需） |
| `app/server.py` | FastAPI 应用装配：挂 `/api/v1`、WebSocket，并把前端挂在 `/` |
| `app/requirements.txt` | 运行依赖，从 `app/pyproject.toml` 抄出（该项目的 setuptools 配置不适合 `pip install .`） |
| `app/ui/` | 前端源码：React 19 + MUI 7 + TanStack Router/Query + zustand，rsbuild 构建，产物进 `app/ui/dist` |
| `Dockerfile` | 两阶段：node 构建前端 → python:3.13 运行 |
| `entrypoint.sh` | API Key、用户数据目录、Qt 离屏、代理变量清理、PUID/PGID 降权 |
| `unraid/mdcx-web.xml` | Unraid Docker 模板 |
| `unraid/icon.png` | 模板图标（`scripts/make_icon.py` 生成） |
| `docs/API-CONTRACT.md` | 接口与容器变量契约（前后端唯一契约来源） |
| `scripts/smoke_test.py` | 部署后自检 |

## 相对上游改了什么

1. **`app/mdcx/server/config.py`** — 上游写的是 `api_key_: str | None = Field(default=None, init_var=True)`。`init_var=True` 让该字段只接受构造参数、完全不读环境变量，而文件末尾在模块级就实例化了 `Config()`，于是 `MDCX_API_KEY` 永远读不到，服务端启动必然 `ValidationError` 后 `exit(1)`。改回普通字段 `api_key`（环境变量 `MDCX_API_KEY`），下游只用到模块级常量 `API_KEY`，无其他影响。
2. **`app/mdcx/server/api/v1/legacy.py`** — 新增 `POST /api/v1/legacy/scrape/cancel`（`operation_id=cancelScrape`）。上游只有开始刮削，没有停止；桌面版靠按钮回调，Web 端缺这个入口。
3. **`app/requirements.txt`** — 新增，见上。
4. **`app/ui/`** — 补「停止刮削」按钮（二次确认）、进度条、成功/失败/当前番号三视图；视觉改为玻璃态暗色；修掉生产构建下 `import.meta.env` 未定义导致的白屏。
6. 修正源码里 6 处把「服务端不可达」写成事实的注释（`mdcx/server/var.py`、`mdcx/server/signals.py`、`mdcx/server/ws/types.py`、`mdcx/server/ws/manager.py`，以及 `mdcx/config/models.py`、`mdcx/signals.py` 里各自那段说明）——那是上一轮静态分析的残留判断（自称「全库 uvicorn/FastAPI 0 命中」），实际服务端路径完全可用，已实测。
7. **`app/server.py`** — 前端 SPA 深链接回退。原来 `app.mount("/", StaticFiles(..., html=True))` 只把目录请求映射到 index.html，不含通配回落，于是在 `/tool`、`/results`、`/logs` 上按 F5 直接 404。改为 `/static` 挂静态资源 + 显式 catch-all 返回 `index.html`，并让 `api/` 前缀保持 404 JSON 语义（免得接口调错时拿到一坨 HTML）。

## 构建

```bash
docker build -t mdcx-web .
```

## 运行

```bash
docker run -d --name mdcx-web \
  -p 8000:8000 \
  -v /mnt/user/appdata/mdcx-web:/config \
  -v /mnt/user/media:/media \
  -v /mnt/user/media/output:/output \
  -e PUID=99 -e PGID=100 -e TZ=Asia/Shanghai \
  mdcx-web
```

打开 `http://<host>:8000`，在登录页填入 API Key。

### API Key 怎么来

按优先级三选一：

1. 环境变量 `MDCX_API_KEY`（模板里填了就固定用它）；
2. 留空 → 首次启动自动生成随机值，持久化到 `/config/api_key`，并打印在容器日志里；
3. 想找回：`cat /mnt/user/appdata/mdcx-web/api_key`。

### 环境变量

| 变量 | 默认 | 说明 |
|---|---|---|
| `MDCX_API_KEY` | 空 → 自动生成 | 访问 API/WebSocket 的密钥，走 `X-API-KEY` 请求头 |
| `MDCX_SAFE_DIRS` | `/media,/output,/config` | 允许浏览/写入的目录白名单，逗号分隔；入口脚本会 `mkdir -p` |
| `MDCX_HOST` | `0.0.0.0` | 监听地址 |
| `MDCX_PORT` | `8000` | 监听端口 |
| `PUID` / `PGID` | `99` / `100` | Unraid 的 nobody:users |
| `TZ` | `Asia/Shanghai` | 时区 |
| `UMASK` | `002` | 新建文件权限掩码 |

卷：`/config`（持久化，必挂）、`/media`（片源，必挂）、`/output`（输出，必挂）。

## Unraid

模板 `unraid/mdcx-web.xml` 通过 jsdelivr 分发：

```
https://cdn.jsdelivr.net/gh/squallnk/mdcx-web@main/unraid/mdcx-web.xml
```

详见 `unraid/README.md`。

## 自检

容器起来后：

```bash
python scripts/smoke_test.py http://127.0.0.1:8000 <api-key>
```

它会验证：未鉴权被拒（401）、WebSocket 连接表可读、配置可读、目录浏览可用、前端静态页已挂载、停止刮削端点真实可调。任一失败以非 0 退出。

## 已知边界

- **不能搬**：本地播放器打开、资源管理器定位、系统托盘、全局快捷键——桌面专属。
- 选目录走服务端 `GET /api/v1/files/list`，受 `MDCX_SAFE_DIRS` 限制，浏览器拿不到本地路径。
- 封面裁剪在前端 canvas 做，不再走本地图片编辑器。
- `ping3` 的网络连通性检测在容器内非 root 运行时可能因缺 ICMP 权限失效，不影响刮削主流程。

## 镜像

```
ghcr.io/squallnk/mdcx-web:latest
```

匿名可拉取（无需 `docker login`）。Actions 每次 push 到 `main` 自动构建。

**只提供 `linux/amd64`**。`PyQt5==5.15.11` 在 Linux arm64 上没有预编译 wheel，pip 会退到 sdist，需要整套 Qt5 构建工具链（qmake / qtbase5-dev），体积和失败面都不划算；Unraid 主机实际都是 x86_64。

## 许可

继承上游 **GPL-3.0**（见 `LICENSE`）。分发镜像时须向使用者提供对应源码，因此本仓库为公开仓库。
