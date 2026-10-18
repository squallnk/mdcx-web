# MDCx-Web · Unraid 模板

镜像 `ghcr.io/squallnk/mdcx-web:latest`，容器内单进程 `uvicorn server:app`，一个 8000 端口同时提供 WebUI、REST API 与 WebSocket。

## 在 Unraid 里添加模板

Unraid 只识别 `templates-user` 目录下以 `my-` 开头的模板文件，把 XML 拉下来即可：

```bash
mkdir -p /boot/config/plugins/dockerMan/templates-user
cd /boot/config/plugins/dockerMan/templates-user
wget -O my-MDCx-Web.xml https://cdn.jsdelivr.net/gh/squallnk/mdcx-web@main/unraid/mdcx-web.xml
```

然后 Docker 页 → **Add Container** → Template 下拉框选 **MDCx-Web**，填好路径后点 Apply。

模板地址（jsdelivr 原始链接）：

```
https://cdn.jsdelivr.net/gh/squallnk/mdcx-web@main/unraid/mdcx-web.xml
```

> jsdelivr 只代理**公开**仓库。仓库还是私有的时候该链接会 404，此时可以先用带 token 的方式拉取，或把 `unraid/mdcx-web.xml` 直接拷进上面的目录：
> `curl -H "Authorization: token <你的PAT>" -o my-MDCx-Web.xml https://raw.githubusercontent.com/squallnk/mdcx-web/main/unraid/mdcx-web.xml`

## 必填项

| 项 | 容器路径 | 说明 |
|---|---|---|
| `MOVIE_PATH` | `/media` | 待刮削影片目录。**必填** |
| `OUTPUT_PATH` | `/output` | 刮削输出目录（nfo、图片、软链接）。**必填** |
| `CONFIG_PATH` | `/config` | 配置持久化目录，存 `config.json` 和 `api_key`，不要删。默认 `/mnt/user/appdata/mdcx-web` |
| `MDCX_SAFE_DIRS` | — | 默认 `/media,/output,/config`，改动挂载点后要同步改这里 |

入口脚本会对 `MDCX_SAFE_DIRS` 里每一项执行 `mkdir -p`，所以宿主目录不存在也能启动；但路径填错会表现为刮削时读不到片源。

`PUID` / `PGID` 默认 `99` / `100`（Unraid 的 nobody / users），保持默认即可正常读写。

## 首次启动：拿 API key

`MDCX_API_KEY` 留空时，入口脚本会生成一个随机密钥，持久化到 `/config/api_key`，并打印到容器日志。三种取法任选：

- Unraid Docker 页 → 点容器图标 → **Logs**，找 `API key` 那一行；
- 终端：`docker logs MDCx-Web 2>&1 | grep -i 'api.key'`；
- 直接读文件：`cat /mnt/user/appdata/mdcx-web/api_key`。

想让密钥固定不随机，启动前把 `MDCX_API_KEY` 填成自己的值即可。

## 登录页怎么用这个 key

浏览器打开 `http://<NAS-IP>:8000/` 会先跳到登录页，把上面拿到的 key 粘进去登录。前端会把它保存下来，之后所有 API 请求都带 `X-API-KEY` 请求头，WebSocket 也用它鉴权。

用 curl 手动验证：

```bash
curl -H "X-API-KEY: <你的key>" http://<NAS-IP>:8000/api/v1/ws/connections
```
