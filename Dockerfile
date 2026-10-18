# syntax=docker/dockerfile:1.7

# ---------- 阶段 1：构建前端 ----------
# ui/ 是 React 19 + MUI 7 + rsbuild 工程，产物必须在 dist/（server.py 挂的是 ui/dist）。
FROM node:22-alpine AS frontend
WORKDIR /ui
# 与本地验证过的版本一致：pnpm 11 才认 pnpm-workspace.yaml 里的 allowBuilds 键，
# 用 pnpm 10 会因 esbuild/core-js 的构建脚本被忽略而让 build 失败。
RUN npm install -g pnpm@11
COPY app/ui/package.json app/ui/pnpm-lock.yaml app/ui/pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile
COPY app/ui/ ./
RUN pnpm build && test -f dist/index.html

# ---------- 阶段 2：运行时 ----------
FROM python:3.13-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=Asia/Shanghai \
    QT_QPA_PLATFORM=offscreen \
    MDCX_HOST=0.0.0.0 \
    MDCX_PORT=8000 \
    MDCX_SAFE_DIRS=/media,/output,/config

# PyQt5 在 Linux 需要 OpenGL/xkb/fontconfig 一整套运行时库；
# fonts-noto-cjk 用于中文界面；gosu 用于 PUID/PGID 降权；tzdata 用于 TZ。
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 libegl1 libxkbcommon0 libdbus-1-3 libfontconfig1 libglib2.0-0 \
        fonts-noto-cjk tzdata gosu \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 依赖清单从 pyproject.toml 抄出（见文件内注释），单独一层便于缓存。
COPY app/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt

# 只把运行时需要的部分进镜像；ui 源码留在构建阶段。
COPY app/mdcx ./mdcx
COPY app/resources ./resources
COPY app/server.py ./
COPY --from=frontend /ui/dist ./ui/dist
# GPL-3.0 要求随二进制分发许可证原文
COPY LICENSE ./LICENSE

# 降权用的用户/组，名字必须与 entrypoint.sh 里的 groupmod/usermod 一致（都叫 mdcx）。
# 用 -o 允许 gid/uid 已被系统占用（Debian 的 users 组就占着 gid 100）；不用 --system，
# 否则 uid 99 不在系统 uid 范围（100-999）里会被拒。装机失败也不致命：
# entrypoint 会按需重建，最坏回退 root 运行。
RUN groupadd -o -g 100 mdcx 2>/dev/null || true \
    && useradd -o -u 99 -g 100 -M -s /usr/sbin/nologin mdcx 2>/dev/null || true \
    && mkdir -p /config /media /output \
    && chown -R 99:100 /config 2>/dev/null || true

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

VOLUME ["/config"]
EXPOSE 8000

# entrypoint 会 export MDCX_API_KEY 给 uvicorn，但 healthcheck 是独立进程读不到，
# 所以从持久化文件取 key。
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request as u; k=open('/config/api_key').read().strip(); r=u.Request('http://127.0.0.1:8000/api/v1/ws/connections', headers={'X-API-KEY': k}); u.urlopen(r, timeout=4)" || exit 1

ENTRYPOINT ["/entrypoint.sh"]
# --host/--port 不写在这里：entrypoint.sh 会按 MDCX_HOST/MDCX_PORT 追加，
# 否则模板里改端口对 uvicorn 不生效。
CMD ["uvicorn", "server:app"]
