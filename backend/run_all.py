"""Pazandani to'liq ishga tushiradi va ishlab turishini kuzatadi.

1. frontend/dist eskirgan bo'lsa qayta yig'adi (npm run build)
2. API + Mini App: uvicorn 127.0.0.1:8000
3. Cloudflare tunnel -> https://<tasodifiy>.trycloudflare.com (har ishga tushganda yangi manzil)
4. Telegram bot shu manzil bilan (menyu tugmasi yangilanadi)

Biror qism to'xtab qolsa, qayta ishga tushiriladi; tunnel manzili o'zgarsa bot ham yangilanadi.

    pythonw run_all.py          # konsolsiz (avtoyuklash shu tarzda ishlaydi)
    python run_all.py --stop    # ishlab turgan nusxani to'xtatish
Loglar: backend/logs/
"""

import logging
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
from logging.handlers import RotatingFileHandler
from pathlib import Path

BACKEND = Path(__file__).resolve().parent
FRONTEND = BACKEND.parent / "frontend"
LOGS = BACKEND / "logs"
PID_FILE = LOGS / "run_all.pid"
PORT = 8000
HEALTH_URL = f"http://127.0.0.1:{PORT}/api/health"
TUNNEL_URL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
# pythonw ostida bolalar jarayonlari ham konsolsiz ishlashi uchun
PYTHON = Path(sys.executable).with_name("pythonw.exe") if os.name == "nt" else Path(sys.executable)
if not PYTHON.exists():
    PYTHON = Path(sys.executable)

LOGS.mkdir(exist_ok=True)
log = logging.getLogger("run_all")
log.setLevel(logging.INFO)
_handler = RotatingFileHandler(LOGS / "run_all.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8")
_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
log.addHandler(_handler)
if sys.stdout and sys.stdout.isatty():
    log.addHandler(logging.StreamHandler(sys.stdout))


def find_cloudflared() -> str:
    candidates = [
        shutil.which("cloudflared"),
        os.path.expandvars(r"%ProgramFiles(x86)%\cloudflared\cloudflared.exe"),
        os.path.expandvars(r"%ProgramFiles%\cloudflared\cloudflared.exe"),
    ]
    for c in candidates:
        if c and Path(c).exists():
            return c
    raise SystemExit("cloudflared topilmadi: winget install --id Cloudflare.cloudflared")


def api_alive() -> bool:
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=2) as r:
            return r.status == 200
    except OSError:
        return False


def build_frontend() -> None:
    """dist yo'q yoki src undan yangiroq bo'lsa, frontendni qayta yig'adi."""
    index = FRONTEND / "dist" / "index.html"
    sources = [p for p in (FRONTEND / "src").rglob("*") if p.is_file()] + [FRONTEND / "index.html"]
    if index.exists() and max(p.stat().st_mtime for p in sources) <= index.stat().st_mtime:
        return
    npm = shutil.which("npm.cmd") or shutil.which("npm")
    if not npm:
        log.error("npm topilmadi — frontend yig'ilmadi")
        return
    log.info("Frontend yig'ilmoqda...")
    with open(LOGS / "build.log", "w", encoding="utf-8") as out:
        subprocess.run([npm, "run", "build"], cwd=FRONTEND, stdout=out, stderr=subprocess.STDOUT, creationflags=NO_WINDOW)


class Child:
    def __init__(self, name: str):
        self.name = name
        self.proc: subprocess.Popen | None = None

    def alive(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def stop(self) -> None:
        if self.alive():
            self.proc.terminate()
            try:
                self.proc.wait(10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        self.proc = None


class Api(Child):
    def start(self) -> None:
        out = open(LOGS / "api.log", "a", encoding="utf-8")
        self.proc = subprocess.Popen(
            [str(PYTHON), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(PORT), "--no-access-log"],
            cwd=BACKEND, stdout=out, stderr=subprocess.STDOUT, creationflags=NO_WINDOW,
        )
        for _ in range(30):
            if api_alive():
                log.info("API ishga tushdi (port %s)", PORT)
                return
            time.sleep(1)
        log.error("API 30 soniyada javob bermadi, logs/api.log ni ko'ring")


class Tunnel(Child):
    def __init__(self):
        super().__init__("tunnel")
        self.url: str | None = None
        self._found = threading.Event()

    def start(self) -> None:
        self.url = None
        self._found.clear()
        self.proc = subprocess.Popen(
            [find_cloudflared(), "tunnel", "--no-autoupdate", "--url", f"http://127.0.0.1:{PORT}"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
            creationflags=NO_WINDOW,
        )
        threading.Thread(target=self._read, args=(self.proc,), daemon=True).start()
        if self._found.wait(60):
            log.info("Tunnel manzili: %s", self.url)
        else:
            log.error("Tunnel manzili 60 soniyada olinmadi, logs/tunnel.log ni ko'ring")

    def _read(self, proc: subprocess.Popen) -> None:
        with open(LOGS / "tunnel.log", "a", encoding="utf-8") as out:
            for line in proc.stdout:
                out.write(line)
                out.flush()
                if not self._found.is_set() and (m := TUNNEL_URL_RE.search(line)):
                    self.url = m.group(0)
                    self._found.set()


class Bot(Child):
    def start(self, url: str) -> None:
        out = open(LOGS / "bot.log", "a", encoding="utf-8")
        env = {**os.environ, "WEBAPP_URL": url}
        self.proc = subprocess.Popen(
            [str(PYTHON), "bot.py"], cwd=BACKEND, env=env, stdout=out, stderr=subprocess.STDOUT, creationflags=NO_WINDOW,
        )
        log.info("Bot ishga tushdi: %s", url)


def wait_for_internet() -> None:
    """Kompyuter yoqilganda tarmoq darhol tayyor bo'lmasligi mumkin."""
    for _ in range(120):
        try:
            urllib.request.urlopen("https://api.telegram.org", timeout=5)
            return
        except OSError as e:
            if getattr(e, "code", None):  # HTTP javob keldi — internet bor
                return
            time.sleep(5)


def stop_running() -> None:
    if not PID_FILE.exists():
        print("Ishlab turgan nusxa topilmadi")
        return
    pid = PID_FILE.read_text().strip()
    subprocess.run(["taskkill", "/PID", pid, "/T", "/F"], capture_output=True)
    PID_FILE.unlink(missing_ok=True)
    print(f"To'xtatildi (PID {pid})")


def main() -> None:
    if "--stop" in sys.argv:
        stop_running()
        return
    if api_alive():
        log.info("Port %s band — Pazanda allaqachon ishlayapti, chiqamiz", PORT)
        return
    PID_FILE.write_text(str(os.getpid()))
    log.info("==== Pazanda ishga tushmoqda ====")
    wait_for_internet()
    build_frontend()

    api, tunnel, bot = Api("api"), Tunnel(), Bot("bot")
    api.start()
    tunnel.start()
    if tunnel.url:
        bot.start(tunnel.url)

    try:
        while True:
            time.sleep(10)
            if not api.alive():
                log.warning("API to'xtadi — qayta ishga tushirilmoqda")
                api.start()
            if not tunnel.alive() or not tunnel.url:
                log.warning("Tunnel to'xtadi — yangi manzil olinmoqda")
                tunnel.stop()
                tunnel.start()
                bot.stop()
            if tunnel.url and (not bot.alive()):
                if bot.proc is not None:
                    log.warning("Bot to'xtadi (kod %s) — qayta ishga tushirilmoqda", bot.proc.returncode)
                    time.sleep(5)
                bot.start(tunnel.url)
    finally:
        for child in (bot, tunnel, api):
            child.stop()
        PID_FILE.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
