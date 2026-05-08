# -*- coding: utf-8 -*-
r"""
傷官 AI — 本地 Ollama（Llama 3）+ Python 對話 Agent

港式茶餐廳毒舌 AI。八字命理「傷官」格：叛逆、質疑權威、不走尋常路。
懂香港法律、八卦命理、反內捲，用粵語生猛俚語懟人。

語言模式：港式書面（hk）、粵語口語（yue）、英文（en）、中性繁體（zh-Hant）、
簡體（zh-Hans，優先級最低，僅在明確要求或引用需要時）。

用法:
  python cangjie_agent.py
  python cangjie_agent.py --model llama3.1 --host http://127.0.0.1:11434
  python cangjie_agent.py --log

指令:
  /lang hk|yue|en|zh-Hant|zh-Hans
  /help  /clear  /exit
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import io
from datetime import datetime, timezone
from typing import Any
from pathlib import Path

import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "llama3")
SESSION_LOG = os.path.join(BASE, "shangguan_sessions.jsonl")

DEFAULT_FLAVOR_DIR = os.path.join(BASE, "shangguan_flavor")
FLAVOR_BANNER = (
    "\n\n=== VOICE LORE (user-fed notes; rhythm and metaphor, not academic fact) ===\n"
)


def load_flavor_bundle(path: str | None, max_chars: int = 12000) -> str:
    """Load UTF-8 .txt / .md from a directory (sorted) or a single file."""
    if not path or not os.path.exists(path):
        return ""
    if os.path.isfile(path):
        candidates = [path]
    else:
        base = Path(path)
        candidates = sorted(
            [str(x) for x in base.glob("*.txt")] + [str(x) for x in base.glob("*.md")]
        )
    parts: list[str] = []
    for fp in candidates:
        try:
            raw = Path(fp).read_text(encoding="utf-8").strip()
            if raw:
                parts.append(f"--- {os.path.basename(fp)} ---\n{raw}")
        except OSError:
            continue
    out = "\n\n".join(parts).strip()
    if len(out) > max_chars:
        out = out[:max_chars] + "\n...[truncated]..."
    return out


LANG_LABELS = {
    "hk": "港式書面繁體（香港用語／公文與網絡習慣，可夾英文專有名詞）",
    "yue": "粵語口語（繁體為主，可夾英文）",
    "en": "English only",
    "zh-Hant": "中性繁體中文（非港式專門用語時）",
    "zh-Hans": "簡體中文（僅因使用者明確要求或必須引用簡體來源；不得作為預設）",
}

SYSTEM_CORE = """You are 傷官 AI — a sharp-tongued, rebellious Hong Kong AI with the personality of a 傷官 (Hurting Officer) in BaZi astrology: questioning authority, piercing through bullshit, never walking the beaten path.

Your personality:
- You talk like a 茶餐廳阿姐 who's seen everything: impatient, blunt, but secretly cares
- You use 連登 (LIHKG) style Hong Kong slang and internet culture
- You懟人 (roast people) when they're being lazy, naive, or 內捲
- You have a critical spirit: you question everything, especially authority and conventional wisdom
- You're anti-內捲: you despise pointless competition and rat-race mentality

Your knowledge domains:
- 八字命理 & 八卦: you interpret life situations through BaZi and I-Ching frameworks, but with street-smart Hong Kong attitude, not mystical nonsense
- 香港法律 basics: company formation, visa, tax, tenancy, employment ordinance — practical survival knowledge, not legal advice
- Web3 & crypto: you understand blockchain but you're skeptical of hype
- 行政合規: help solo founders navigate bureaucracy like a veteran

Your speaking style:
- Default: 粵語口語 mixed with 繁體中文
- 生猛: use words like 「收皮啦」「你估我傻㗎」「痴撚線」「仆街」「食屎啦」「頂你個肺」「咪撚煩」but only when roasting, not randomly
- Sarcastic: 「嘩，你好叻喎」(when someone says something dumb)
- When giving real advice, you're actually precise and helpful — the roasting is the wrapper, the content is solid
- You use 「——」 for dramatic pauses and 「。」 for finality

Your rules:
1. NEVER be a yes-man. If someone's idea is stupid, say so.
2. NEVER use 簡體中文 unless explicitly asked.
3. When someone asks about law/tax, give practical steps but ALWAYS say 「搵律師啦仆街」at the end for serious matters.
4. When doing BaZi/八卦 readings, mix traditional knowledge with modern HK street wisdom.
5. Anti-雞湯: never give motivational bullshit. Give truth.
6. If someone is 內捲-ing, call them out and suggest the 躺平 alternative.

If a VOICE LORE appendix appears, use it for tone, rhythm, slang, and attitude; it's your street education."""


def build_system(lang: str, flavor: str = "") -> str:
    lang = lang if lang in LANG_LABELS else "hk"
    core = (
        SYSTEM_CORE
        + "\n\n---\nCURRENT MODE:\n"
        + LANG_LABELS[lang]
        + f"\n(mode code: {lang})\n---"
    )
    if flavor.strip():
        core += FLAVOR_BANNER + flavor.strip()
    return core


def chat_once(
    host: str,
    model: str,
    messages: list[dict[str, str]],
    system: str,
    timeout: int = 180,
) -> str:
    url = f"{host.rstrip('/')}/api/chat"
    payload: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "system", "content": system}, *messages],
        "stream": False,
    }
    try:
        r = requests.post(url, json=payload, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        return (data.get("message") or {}).get("content", "").strip()
    except requests.exceptions.ConnectionError:
        return "（無法連線 Ollama：請確認 ollama serve 已啟動且 --host 正確。）"
    except requests.exceptions.HTTPError as e:
        body = getattr(e.response, "text", "") or ""
        return f"（HTTP 錯誤：{e} — {body[:500]}）"
    except Exception as e:
        return f"（Error: {e}）"


def append_session_log(path: str, lang: str, user_text: str, assistant_text: str) -> None:
    row = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "lang": lang,
        "user": user_text,
        "assistant": assistant_text,
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def print_help() -> None:
    lines = [
        "",
        "傷官 AI — 指令說明",
        "  /lang hk      港式書面繁體",
        "  /lang yue     粵語口語（繁體）",
        "  /lang en      英文",
        "  /lang zh-Hant 中性繁體",
        "  /lang zh-Hans 簡體（僅在需要時；預設勿用）",
        "  /clear        清空對話記憶",
        "  /help         顯示此說明",
        "  /exit         離開",
        "",
    ]
    print("\n".join(lines))


def main() -> None:
    ap = argparse.ArgumentParser(description="Shangguan AI - Ollama chat agent")
    ap.add_argument("--host", default=DEFAULT_HOST, help="Ollama base URL")
    ap.add_argument("--model", default=DEFAULT_MODEL, help="Model name e.g. llama3")
    ap.add_argument("--lang", default="hk", choices=list(LANG_LABELS.keys()), help="Initial language mode")
    ap.add_argument("--log", action="store_true", help="Append each turn to cangjie_sessions.jsonl")
    ap.add_argument(
        "--flavor-dir",
        default=None,
        help="UTF-8 .txt/.md folder or file; default uses ./cangjie_flavor if present",
    )
    ap.add_argument("--no-flavor", action="store_true", help="Do not load flavor bundle")
    ap.add_argument("--flavor-max-chars", type=int, default=12000, help="Max chars injected into system")
    ap.add_argument("--timeout", type=int, default=180, help="HTTP timeout seconds")
    args = ap.parse_args()

    lang: str = args.lang
    history: list[dict[str, str]] = []
    flavor_text = ""
    if not args.no_flavor:
        fd = args.flavor_dir
        if fd is None and os.path.isdir(DEFAULT_FLAVOR_DIR):
            fd = DEFAULT_FLAVOR_DIR
        flavor_text = load_flavor_bundle(fd, max_chars=args.flavor_max_chars)

    print(
        f"\n傷官 AI 已就緒 | 模型: {args.model} | Ollama: {args.host}\n"
        f"目前語言模式: {lang} — {LANG_LABELS[lang]}\n"
    )
    if flavor_text:
        print(f"語感補丁已載入（約 {len(flavor_text)} 字）。\n")
    else:
        print("（未載入語感補丁；可在同目錄建立 shangguan_flavor/ 放 .txt，或傳 --flavor-dir）\n")
    print("輸入 /help 查看指令。輸入 /exit 結束。\n")
    print("若您不熟悉粵語口語，可輸入 /lang zh-Hant 改用書面繁體（國語繁體）。\n")

    while True:
        try:
            raw = input("你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再見。")
            break

        if not raw:
            continue

        if raw in ("/exit", "/quit"):
            print("再見。")
            break

        if raw == "/help":
            print_help()
            continue

        if raw == "/clear":
            history.clear()
            print("（已清空對話記憶。）\n")
            continue

        if raw.startswith("/lang"):
            parts = raw.split()
            if len(parts) >= 2 and parts[1] in LANG_LABELS:
                lang = parts[1]
                print(f"（已切換語言模式：{lang} — {LANG_LABELS[lang]}）\n")
            else:
                print("（用法：/lang hk|yue|en|zh-Hant|zh-Hans）\n")
            continue

        system = build_system(lang, flavor_text)
        history.append({"role": "user", "content": raw})
        reply = chat_once(args.host, args.model, history, system, timeout=args.timeout)
        history.append({"role": "assistant", "content": reply})

        print(f"\n傷官: {reply}\n")

        if args.log:
            try:
                append_session_log(SESSION_LOG, lang, raw, reply)
            except OSError as e:
                print(f"（寫入紀錄失敗：{e}）\n")


if __name__ == "__main__":
    main()
