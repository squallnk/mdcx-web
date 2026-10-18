# MDCx Web —— API 与容器契约

> 本文件是前后端两个子任务的**唯一契约来源**。任何一方改动契约，必须先改这里。

## 1. 运行形态

单容器、单进程：`uvicorn server:app`，FastAPI 同时提供 REST、WebSocket 与前端静态文件。

- 运行目录（`MAIN_PATH`，由 `mdcx/consts.py:36` 从 `__file__` 推导）：`/app`
- 前端静态文件：`/app/ui/dist`（`server.py:36` 的 `StaticFiles(directory="ui/dist")` 是**相对 CWD** 的，故 WORKDIR 必须是 `/app`）
- 用户数据目录：`/config`（靠 `/app/MDCx.config` 标记文件重定向，内容就是一行 `/config/config.json`）

### 容器变量契约（Unraid 模板与 CI 都必须与此一致）

| 变量 | 默认 | 说明 |
|---|---|---|
| `MDCX_API_KEY` | 空 → 入口脚本生成 | 访问 API/WS 的 `X-API-KEY`。留空时由 entrypoint 生成随机值并持久化到 `/config/api_key` |
| `MDCX_SAFE_DIRS` | `/media,/output,/config` | 允许浏览/写入的目录白名单，逗号分隔。`mdcx/server/config.py` 会校验每个目录必须存在 |
| `MDCX_HOST` | `0.0.0.0` | 监听地址 |
| `MDCX_PORT` | `8000` | 监听端口 |
| `PUID` | `99` | Unraid nobody |
| `PGID` | `100` | Unraid users |
| `TZ` | `Asia/Shanghai` | 时区 |
| `UMASK` | `002` | 新建文件权限掩码 |

卷：`/config`（持久化，必挂）、`/media`（片源，必挂）、`/output`（输出，必挂）。
端口：`8000`。

镜像：`ghcr.io/squallnk/mdcx-web`。

## 2. REST 端点（全部需要 `X-API-KEY` 请求头，否则 401）

前缀 `/api/v1`。路径**末尾斜杠敏感**（`/config` 会 404，`/config/` 才对）。

### 配置 `/config`

| 方法 | 路径 | operation_id | 说明 |
|---|---|---|---|
| GET | `/config/` | `getCurrentConfig` | 当前配置（`mdcx.config.models.Config`） |
| PUT | `/config/` | `updateConfig` | 保存整个配置对象 |
| GET | `/config/schema` | `getConfigSchema` | JSON Schema，rjsf 表单用 |
| GET | `/config/ui_schema` | `getConfigUISchema` | rjsf uiSchema |
| GET | `/config/default` | `getDefaultConfig` | 默认配置 |
| POST | `/config/reset` | `resetConfig` | 重置为默认 |
| POST | `/config/create?name=` | `createConfig` | 新建配置文件 |
| POST | `/config/switch?name=` | `switchConfig` | 切换配置文件，返回 `{config, errors}` |
| DELETE | `/config/?name=` | `deleteConfig` | 删除配置文件 |

### 文件浏览 `/files`

| 方法 | 路径 | operation_id | 说明 |
|---|---|---|---|
| GET | `/files/list?path=` | `listFiles` | 返回 `{items:[{name,path,type:"file"\|"directory",size,last_modified}], total}`，目录在前、按名不区分大小写排序、最多 1000 项 |

`path` 可为相对路径（基于 `SAFE_DIRS[0]`）。越界返回 403。

### 刮削控制 `/legacy`

| 方法 | 路径 | operation_id | 说明 |
|---|---|---|---|
| POST | `/legacy/scrape` | `startScrape` | 用当前配置开始全量刮削，无参数 |
| POST | `/legacy/scrape/cancel` | `cancelScrape` | **本次新增**。停止当前刮削，返回 `{cancelled: bool, message: str}`。未在刮削时返回 `{cancelled:false}` 而非报错 |
| POST | `/legacy/scrape/single` | `scrapeSingleFile` | body `{path, url}`，单番号刮削 |
| POST | `/legacy/symlink` | `createSymlink` | body `{source_dir, dest_dir, copy_files}` 创建软链接 |
| POST | `/legacy/subtitles` | `addSubtitles` | 检查并添加字幕 |
| GET | `/legacy/actors` | `getActors` | 演员名单（结果走日志） |
| POST | `/legacy/actors/complete` | `completeActors` | 补全演员信息/头像 |
| POST | `/legacy/cookies` | `checkCookies` | 占位，未实现 |
| GET/POST | `/legacy/sites` | `getSiteUrls` / `setSiteUrl` | 站点自定义网址 |

### WebSocket `/ws`

| 方法 | 路径 | 说明 |
|---|---|---|
| WS | `/api/v1/ws/` | 日志与信号推送。鉴权走 `WebSocketProtocolBearerMiddleware`（`mdcx/server/ws/auth.py`），已有前端实现见 `ui/src/hooks/useWebSocket.ts` |
| GET | `/api/v1/ws/connections` | 返回 `{active_connections, connections}`；也用作 API key 探活 |

## 3. WebSocket 消息形状

`mdcx/server/ws/types.py` 的 `WebSocketMessage.to_dict()` 产出：

```json
{
  "type": "qt_signal" | "progress" | "ping" | "pong" | "connect" | ...,
  "data": { "name": "<signal_name>", "data": <payload> },
  "timestamp": "ISO-8601",
  "message_id": "uuid",
  "client_id": null
}
```

`mdcx/server/signals.py:ServerSignals` 实际投递的信号如下（`name` → `data`）：

| name | type | data 形状 | 前端用途 |
|---|---|---|---|
| `log_text` | `qt_signal` | `string` | 日志正文 |
| `detail_log` | `qt_signal` | `string` | 带时间戳的详情日志 |
| `scrape_info` | `qt_signal` | `string` | 刮削阶段提示 |
| `net_info` | `qt_signal` | `string` | 网络请求提示 |
| `set_main_info` | `qt_signal` | `{"show_data": ShowData \| null}` | 当前番号信息卡 |
| `show_list_name` | `qt_signal` | `{"status":"succ"\|"fail", "show_data": ShowData \| null, "real_number": string}` | **成功/失败结果列表** |
| `logs_failed_settext` | `qt_signal` | `string` | 失败面板文本 |
| `view_success_file_settext` | `qt_signal` | `string` | 成功文件文本 |
| `view_failed_list_settext` | `qt_signal` | `string` | 失败列表文本 |
| `logs_failed_show` | `qt_signal` | `string` | 失败详情（含指向文件与原因） |
| — | **`progress`** | `{"progress": int, "total": 100, "percentage": int, "description": "Processing..."}` | **进度条**。注意此消息 `type` 是 `progress`，不是 `qt_signal` |

`ShowData` 定义见 `app/mdcx/models/types.py`（字段含 `number/title/actor/outline/...`，序列化用 `dataclasses.asdict`）。

**前端现状缺口**：`ui/src/App.tsx` 目前只注册了 `qt_signal` 处理器并塞进日志 store，`progress` 与 `show_list_name` / `set_main_info` 全部被丢弃。补功能时按上表分发到独立 store。

## 4. 已确认的坑（务必遵守）

1. 容器内必须 `QT_QPA_PLATFORM=offscreen` 且 `QT_QPA_PLATFORM_PLUGIN_PATH` 指向 PyQt5 的 `Qt5/plugins/platforms`，否则报 `Could not find the Qt platform plugin "offscreen"`。
2. 必须清空所有 `*_PROXY*` 环境变量。本机 `NO_PROXY` 含 `[::1]` 时 httpx 抛 `Invalid port: ':1]'`，整条 import 链崩。容器里继承宿主 proxy 变量会复现同类问题。
3. `/config` 首次启动由 `ConfigManager` 自动写入默认 `config.json`；镜像**不打包** `config.json`（其中含用户账号与 cookie）。
4. `MDCX_SAFE_DIRS` 里每个目录必须真实存在，否则 `mdcx/server/config.py:68` 抛 `以下路径不是有效的目录` 并 `exit(1)`。
