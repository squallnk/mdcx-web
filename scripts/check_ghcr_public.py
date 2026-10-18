"""匿名校验 ghcr 镜像是否可公开拉取（Unraid 用户不做 docker login 也能 pull）。"""

import json
import urllib.error
import urllib.request

REPO = "squallnk/mdcx-web"
ACCEPT = ", ".join(
    [
        "application/vnd.oci.image.index.v1+json",
        "application/vnd.docker.distribution.manifest.list.v2+json",
        "application/vnd.oci.image.manifest.v1+json",
        "application/vnd.docker.distribution.manifest.v2+json",
    ]
)

tok_url = f"https://ghcr.io/token?scope=repository:{REPO}:pull&service=ghcr.io"
try:
    with urllib.request.urlopen(tok_url, timeout=20) as r:
        token = json.load(r)["token"]
    print(f"anonymous token: ok ({len(token)} chars)")
except Exception as e:  # noqa: BLE001
    print(f"anonymous token: FAILED {type(e).__name__}: {e}")
    raise SystemExit(1)

for tag in ("latest", "main"):
    req = urllib.request.Request(
        f"https://ghcr.io/v2/{REPO}/manifests/{tag}",
        headers={"Authorization": f"Bearer {token}", "Accept": ACCEPT},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            body = json.load(r)
            kind = body.get("mediaType", "?")
            n = len(body.get("manifests", body.get("layers", [])))
            print(f"{tag}: {r.status} pullable anonymously — {kind}, {n} entries")
    except urllib.error.HTTPError as e:
        print(f"{tag}: {e.code} -> {'私有包，需要认证才能 pull' if e.code == 401 else 'error'}")
    except Exception as e:  # noqa: BLE001
        print(f"{tag}: {type(e).__name__}: {e}")
