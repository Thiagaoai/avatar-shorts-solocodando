#!/usr/bin/env python3
"""Avatar no HeyGen falando o SEU áudio (lipsync no trecho exato da narração).

Uso:
  python3 avatar.py looks [--filtro texto]   lista seus looks (avatares) privados
  python3 avatar.py whoami                   mostra conta e créditos
  python3 avatar.py criar <projeto>          envia intro.mp3/final.mp3 e cria os 2 vídeos
  python3 avatar.py esperar <projeto>        espera e baixa assets/avatar_intro.mp4 e avatar_final.mp4

Autenticação: HEYGEN_API_KEY no .env (header x-api-key) ou, se não houver, a sessão OAuth em
~/.heygen/credentials (criada por `npx hyperframes auth login`).
"""
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import die, http, load_config, load_env, multipart  # noqa: E402

API = "https://api.heygen.com"


def auth():
    k = os.environ.get("HEYGEN_API_KEY")
    if k:
        return {"x-api-key": k}
    cred = Path.home() / ".heygen" / "credentials"
    try:
        return {"Authorization": "Bearer " + json.loads(cred.read_text())["oauth"]["access_token"]}
    except Exception:
        die("sem HEYGEN_API_KEY no .env e sem login OAuth (rode: npx -y hyperframes@latest auth login).")


def main():
    load_env()
    if len(sys.argv) < 2:
        die(__doc__)
    cmd = sys.argv[1]
    if cmd == "whoami":
        d = http("GET", f"{API}/v3/users/me", auth())["data"]
        cr = d.get("subscription", {}).get("credits", {}).get("premium_credits", {})
        print(json.dumps({"email": d.get("email"), "plano": d.get("subscription", {}).get("plan"), "creditos": cr.get("remaining")}))
    elif cmd == "looks":
        filt = sys.argv[3].lower() if len(sys.argv) > 3 else ""
        tok = None
        while True:
            d = http("GET", f"{API}/v3/avatars/looks?ownership=private&limit=50" + (f"&token={tok}" if tok else ""), auth())
            for x in d.get("data", []):
                if filt in (x.get("name") or "").lower():
                    print(f'{x["id"]}  {x.get("name")}  (engines: {",".join(x.get("supported_api_engines") or [])})')
            tok = d.get("next_token")
            if not d.get("has_more") or not tok:
                break
    elif cmd == "criar":
        proj = Path(sys.argv[2]); cfg = load_config(proj); look = cfg["avatar"]["look_id"]
        if "COLE_AQUI" in look:
            die("preencha avatar.look_id no config.json (liste com: python3 avatar.py looks).")
        jobs = {}
        for part in ("intro", "final"):
            mp3 = proj / "audio" / f"{part}.mp3"
            if not mp3.exists():
                die(f"{mp3} não existe — rode voice.py antes.")
            asset = multipart(f"{API}/v3/assets", auth(), "file", mp3, "audio/mpeg")["data"]
            body = {"type": "avatar", "avatar_id": look, "audio_asset_id": asset["asset_id"],
                    "title": f"{proj.name} - {part}", "aspect_ratio": "9:16", "resolution": "1080p"}
            if cfg["avatar"].get("engine"):
                body["engine"] = {"type": cfg["avatar"]["engine"]}
            jobs[part] = http("POST", f"{API}/v3/videos", auth(), body)["data"]["video_id"]
            print(f"{part}: video_id {jobs[part]}")
        (proj / "avatar_jobs.json").write_text(json.dumps(jobs, indent=2))
    elif cmd == "esperar":
        proj = Path(sys.argv[2]); jobs = json.loads((proj / "avatar_jobs.json").read_text())
        (proj / "assets").mkdir(exist_ok=True)
        t0 = time.time()
        for part, vid in jobs.items():
            out = proj / "assets" / f"avatar_{part}.mp4"
            while not out.exists():
                d = http("GET", f"{API}/v3/videos/{vid}", auth())["data"]
                st = d.get("status")
                if st == "completed":
                    urllib.request.urlretrieve(d["video_url"], out)
                    print(f"{part}: pronto ({d.get('duration')}s) → {out}")
                elif st == "failed":
                    die(f"{part} falhou: {d.get('failure_code')} {d.get('failure_message')}")
                elif time.time() - t0 > 1500:
                    die(f"{part} ainda '{st}' depois de 25 min — rode 'esperar' de novo mais tarde.")
                else:
                    time.sleep(20)
    else:
        die(__doc__)


if __name__ == "__main__":
    main()
