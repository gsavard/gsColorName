"""Client minimal compatible OpenAI pour LM Studio et OpenRouter (stdlib uniquement)."""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

PROVIDERS = {
    "LM Studio (local)": {"url": "http://localhost:1234/v1", "needs_key": False},
    "OpenRouter": {"url": "https://openrouter.ai/api/v1", "needs_key": True},
}

SYSTEM_PROMPT = (
    "Tu es un expert en colorimétrie, en design graphique et en impression. "
    "Tu réponds en français, de façon concise et structurée en Markdown. "
    "Quand tu donnes des équivalences dans des nuanciers propriétaires (Pantone, RAL, NCS, "
    "Benjamin Moore, Sico, etc.), précise toujours qu'elles sont approximatives."
)


def _headers(key: str | None):
    h = {"Content-Type": "application/json", "X-Title": "gsColorName"}
    if key:
        h["Authorization"] = f"Bearer {key}"
    return h


def _request(url, key, payload=None, timeout=120):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=_headers(key),
                                 method="POST" if data else "GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:500]
        raise RuntimeError(f"HTTP {e.code} : {body}") from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"Connexion impossible à {url} : {e.reason}") from None


def list_models(base_url: str, key: str | None = None) -> list[str]:
    j = _request(base_url.rstrip("/") + "/models", key, timeout=20)
    return sorted(m.get("id", "") for m in j.get("data", []) if m.get("id"))


def chat(base_url: str, key: str | None, model: str, messages: list[dict],
         temperature: float = 0.4) -> str:
    payload = {"model": model, "messages": messages, "temperature": temperature}
    j = _request(base_url.rstrip("/") + "/chat/completions", key, payload)
    if "error" in j:
        raise RuntimeError(str(j["error"]))
    txt = j["choices"][0]["message"].get("content") or ""
    # retire le raisonnement des modèles « thinking » (Qwen, DeepSeek…)
    txt = re.sub(r"<think>.*?</think>", "", txt, flags=re.S).strip()
    return txt


def color_prompt(color, local_names: list[tuple[float, str, str]], css, fr) -> str:
    fmt = "\n".join(f"- {k} : {v}" for k, v in color.formats()[:12])
    near = "\n".join(f"- {n} ({'#' + h.upper()}, ΔE2000 {d:.1f})" for d, n, h in local_names[:6])
    return (
        f"Voici une couleur :\n{fmt}\n\n"
        f"Noms trouvés localement (base anglaise color-name-list) :\n{near}\n"
        f"Nom CSS le plus proche : {css[0][1]} (ΔE {css[0][0]:.1f})\n"
        f"Nom français de base le plus proche : {fr[0][1]} (ΔE {fr[0][0]:.1f})\n\n"
        "Donne-moi :\n"
        "1. **Nom en français** le plus juste (et 2–3 alternatives)\n"
        "2. **Nom en anglais** courant\n"
        "3. **Famille / description** (teinte, saturation, clarté, chaud/froid)\n"
        "4. **Équivalents approximatifs** : Pantone, RAL Classic, NCS (si pertinent)\n"
        "5. **Remarques d'impression** (gamut CMJN, risque de virage)\n"
        "6. **Associations** : 3 couleurs qui s'accordent bien (avec code HEX)\n"
    )
