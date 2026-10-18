#!/usr/bin/env bash
# MDCx Web 容器入口。
# 职责：把 mdcx 的用户数据目录固定到 /config、决定 API key、准备 Qt 离屏环境、降权到 PUID:PGID。
set -euo pipefail

log() { printf '[entrypoint] %s\n' "$*"; }

umask "${UMASK:-002}"

CONFIG_DIR="${CONFIG_DIR:-/config}"
mkdir -p "$CONFIG_DIR"

# ---- API key：环境变量 / 已持久化 / 新生成，三选一 ----
KEY_FILE="$CONFIG_DIR/api_key"
if [ -n "${MDCX_API_KEY:-}" ]; then
    KEY="$MDCX_API_KEY"
    log "使用环境变量 MDCX_API_KEY"
elif [ -s "$KEY_FILE" ]; then
    KEY="$(cat "$KEY_FILE")"
    log "复用已持久化的 API key"
else
    KEY="$(od -An -tx1 -N24 /dev/urandom | tr -d ' \n')"
    log "已生成新的 API key"
fi
printf '%s' "$KEY" >"$KEY_FILE"
chmod 600 "$KEY_FILE" 2>/dev/null || true
export MDCX_API_KEY="$KEY"

# ---- 用户数据目录指向持久化卷 ----
# mdcx/config/manager.py 读 /app/MDCx.config，其内容即当前配置文件的绝对路径；
# 该文件的父目录同时被当作 userdata 目录（见 mdcx/config/resources.py:30）。
printf '%s' "$CONFIG_DIR/config.json" >/app/MDCx.config

# ---- 白名单目录必须真实存在 ----
# mdcx/server/config.py 校验每个 SAFE_DIRS 条目 is_dir()，否则 print + exit(1)。
IFS=',' read -r -a SAFE_DIRS_ARR <<<"${MDCX_SAFE_DIRS:-/media,/output,$CONFIG_DIR}"
for d in "${SAFE_DIRS_ARR[@]}"; do
    [ -n "$d" ] && mkdir -p "$d"
done

# ---- Qt 离屏 ----
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-offscreen}"
if [ -z "${QT_QPA_PLATFORM_PLUGIN_PATH:-}" ]; then
    QT_QPA_PLATFORM_PLUGIN_PATH="$(python -c 'import os, PyQt5; print(os.path.join(os.path.dirname(PyQt5.__file__), "Qt5", "plugins", "platforms"))')"
    export QT_QPA_PLATFORM_PLUGIN_PATH
fi

# ---- 清掉宿主透传的代理变量 ----
# NO_PROXY 里出现 `[::1]` 这类 IPv6 字面量时 httpx 会抛 `Invalid port: ':1]'`，整条 import 链崩。
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy NO_PROXY no_proxy 2>/dev/null || true

log "配置文件   : $CONFIG_DIR/config.json"
log "可访问目录 : ${MDCX_SAFE_DIRS:-/media,/output,$CONFIG_DIR}"
log "API key    : $KEY"
log "网页登录时把上面的 API key 填进登录框即可。"

# ---- uvicorn 监听地址 ----
# CMD 里不写死 --host/--port，交给这里拼接，Unraid 模板改 MDCX_PORT 才真的生效。
if [ "${1:-}" = "uvicorn" ]; then
    set -- "$@" --host "${MDCX_HOST:-0.0.0.0}" --port "${MDCX_PORT:-8000}"
fi

# ---- 降权到 PUID:PGID ----
# 镜像构建时用户/组可能因为 uid/gid 已被占用而创建失败，所以这里按需重建；
# 任何一步失败都退回 root 继续跑，绝不因为降权失败就让容器启动即退出。
if [ "$(id -u)" = "0" ] && { [ "${PUID:-0}" != "0" ] || [ "${PGID:-0}" != "0" ]; }; then
    PUID="${PUID:-99}"
    PGID="${PGID:-100}"

    getent group mdcx >/dev/null 2>&1 || groupadd -o -g "$PGID" mdcx 2>/dev/null || true
    groupmod -o -g "$PGID" mdcx 2>/dev/null || true
    getent passwd mdcx >/dev/null 2>&1 \
        || useradd -o -u "$PUID" -g "$PGID" -M -s /usr/sbin/nologin mdcx 2>/dev/null || true
    usermod -o -u "$PUID" -g "$PGID" mdcx 2>/dev/null || true

    chown -R "$PUID:$PGID" "$CONFIG_DIR" 2>/dev/null || true

    if getent passwd mdcx >/dev/null 2>&1; then
        exec gosu "$PUID:$PGID" "$@"
    fi
    log "无法降权到 ${PUID}:${PGID}（用户创建失败），继续以 root 运行"
fi

exec "$@"
