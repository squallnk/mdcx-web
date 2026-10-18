"""MDCx Web 冒烟自检：对运行中的服务做真实 HTTP 探测（不经 TestClient）。

用法:
    python scripts/smoke_test.py [base_url] [api_key]

base_url 缺省为 $MDCX_BASE_URL 或 http://127.0.0.1:8000
api_key  缺省依次尝试 $MDCX_API_KEY、/config/api_key

覆盖：鉴权拦截、WebSocket 连接表、配置读取、目录浏览、前端静态页、SPA 深链接回落、
API 404 语义、停止刮削端点。任一失败以非 0 退出，可直接用于健康检查或 CI。
"""

import os
import sys
import urllib.error
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else os.environ.get("MDCX_BASE_URL", "http://127.0.0.1:8000")).rstrip("/")
KEY = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("MDCX_API_KEY", "")
if not KEY:
    try:
        with open("/config/api_key", encoding="utf-8") as f:
            KEY = f.read().strip()
    except OSError:
        KEY = ""

failures: list[str] = []


def call(path: str, key: str = "", method: str = "GET") -> tuple[int, str]:
    headers = {"X-API-KEY": key} if key else {}
    req = urllib.request.Request(BASE + path, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.read(40000).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read(300).decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        return 0, f"{type(e).__name__}: {e}"


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}{(' — ' + detail) if detail else ''}")
    if not ok:
        failures.append(name)


def is_html(body: str) -> bool:
    return "<html" in body.lower() or "<!doctype" in body.lower()


status, _ = call("/api/v1/ws/connections")
check("未鉴权应被拒绝 (401)", status == 401, f"got {status}")

status, body = call("/api/v1/ws/connections", KEY)
check("WebSocket 连接表可读", status == 200 and "active_connections" in body, f"got {status}")

status, body = call("/api/v1/config/", KEY)
check("配置可读", status == 200 and body.lstrip().startswith("{"), f"got {status}")

status, body = call("/api/v1/files/list?path=.", KEY)
check("目录浏览可用", status == 200 and '"items"' in body, f"got {status}")

status, body = call("/")
check("前端静态页已挂载", status == 200 and is_html(body), f"got {status}")

# 前端是 SPA，子路由在磁盘上没有对应文件，刷新时必须回落 index.html 而不是 404
status, body = call("/results")
check("SPA 深链接可刷新", status == 200 and is_html(body), f"got {status}")

# 反过来，不存在的 API 路径不能落到 index.html，否则调用方拿到一坨 HTML 难以排查
status, body = call("/api/v1/__nonexistent__", KEY)
check("未知 API 路径返回 404 JSON", status == 404 and "detail" in body, f"got {status} {body[:60]}")

# 真打一次停止：未在刮削时应返回 {"cancelled": false} 而不是报错。
status, body = call("/api/v1/legacy/scrape/cancel", KEY, method="POST")
check("停止刮削端点可用", status == 200 and '"cancelled"' in body, f"got {status} {body[:80]}")

print()
if failures:
    print(f"FAILED {len(failures)}: {', '.join(failures)}")
    sys.exit(1)
print(f"OK — {BASE} 全部检查通过")
