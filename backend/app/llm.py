"""Gemini API integratsiyasi: matnni masalliqlarga ajratish, yangi retseptni Google qidiruvi orqali topish, suhbat."""

import json
import logging

from google import genai
from google.genai import errors, types

from .config import settings
from .ingredients import CATALOG, CATEGORIES
from .persona import PERSONA_SYSTEM

log = logging.getLogger(__name__)


class LLMUnavailable(Exception):
    pass


_client: genai.Client | None = None


def enabled() -> bool:
    return settings.llm_enabled and bool(settings.gemini_api_key)


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def _generate(contents, *, system: str, thinking: types.ThinkingLevel = types.ThinkingLevel.LOW, **config) -> types.GenerateContentResponse:
    if not enabled():
        raise LLMUnavailable("LLM o'chirilgan yoki API kalit yo'q")
    try:
        response = _get_client().models.generate_content(
            model=settings.gemini_model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system,
                thinking_config=types.ThinkingConfig(thinking_level=thinking),
                **config,
            ),
        )
    except errors.ClientError as e:
        # 429 — bepul tarif limiti (daqiqalik yoki kunlik) tugadi
        if e.code == 429:
            log.warning("Gemini limiti tugadi: %s", e.message)
            raise LLMUnavailable("rate_limit") from e
        log.error("Gemini so'rov xatosi %s: %s", e.code, e.message)
        raise LLMUnavailable(f"api_error_{e.code}") from e
    except errors.ServerError as e:
        log.error("Gemini server xatosi %s: %s", e.code, e.message)
        raise LLMUnavailable(f"server_error_{e.code}") from e
    except errors.APIError as e:
        log.error("Gemini xatosi %s: %s", e.code, e.message)
        raise LLMUnavailable("api_error") from e
    except OSError as e:
        log.error("Gemini bilan aloqa yo'q: %s", e)
        raise LLMUnavailable("connection") from e

    candidate = response.candidates[0] if response.candidates else None
    if candidate is None or candidate.finish_reason not in (types.FinishReason.STOP, types.FinishReason.MAX_TOKENS):
        reason = candidate.finish_reason if candidate else response.prompt_feedback
        log.warning("Gemini javob bermadi: %s", reason)
        raise LLMUnavailable("blocked")
    return response


def _json(response: types.GenerateContentResponse) -> dict:
    if response.candidates[0].finish_reason == types.FinishReason.MAX_TOKENS:
        raise LLMUnavailable("max_tokens")
    try:
        return json.loads(response.text or "")
    except json.JSONDecodeError as e:
        raise LLMUnavailable("invalid_json") from e


def _json_config(schema: dict) -> dict:
    return {"response_mime_type": "application/json", "response_json_schema": schema}


_CATALOG_HINT = "\n".join(
    f"- {i.name} ({CATEGORIES[i.category]})" + (f", 1 ta ≈ {int(i.piece_g)} g" if i.piece_g else "")
    for i in CATALOG
)

# ---------------------------------------------------------------- ombor matnini ajratish

STOCK_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "grams": {"type": "number"},
                    "category": {"type": "string", "enum": list(CATEGORIES)},
                },
                "required": ["name", "grams", "category"],
            },
        },
        "unknown": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["items", "unknown"],
}

STOCK_SYSTEM = f"""Foydalanuvchi bozordan yoki do'kondan olib kelgan oziq-ovqat mahsulotlarini erkin matnda yozadi
(o'zbek lotin yoki kirill yozuvida, ba'zan ruscha so'zlar bilan). Har bir mahsulotni ajratib, miqdorini GRAMMga o'gir.

Qoidalar:
- name: o'zbek lotin yozuvida, kichik harflarda. Agar mahsulot quyidagi katalogda bo'lsa, AYNAN katalogdagi nomni ishlat.
- Dona/ta/bosh/bog' bilan berilgan miqdorni odatiy og'irlik bo'yicha grammga o'gir (katalogdagi qiymatlardan foydalan).
- Litr: suv/sut ≈ 1000 g, o'simlik yog'i ≈ 920 g.
- Miqdor ko'rsatilmagan bo'lsa, oddiy xarid miqdorini taxmin qil (masalan, 1 bog' ko'kat, 1 kg sabzavot).
- Mahsulot bo'lmagan yoki tushunarsiz qismlarni "unknown" ro'yxatiga yoz.

Katalog:
{_CATALOG_HINT}"""


def parse_stock(text: str) -> tuple[list[dict], list[str]]:
    response = _generate(text, system=STOCK_SYSTEM, max_output_tokens=4000, **_json_config(STOCK_SCHEMA))
    data = _json(response)
    items = [i for i in data.get("items", []) if i.get("grams", 0) > 0 and str(i.get("name", "")).strip()]
    return items, data.get("unknown", [])


# ---------------------------------------------------------------- yangi retsept (RAG)

RECIPE_SCHEMA = {
    "type": "object",
    "properties": {
        "is_uzbek_dish": {"type": "boolean"},
        "name": {"type": "string"},
        "aliases": {"type": "array", "items": {"type": "string"}},
        "description": {"type": "string"},
        "time_minutes": {"type": "integer"},
        "ingredients": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "grams_per_person": {"type": "number"},
                    "optional": {"type": "boolean"},
                },
                "required": ["name", "grams_per_person", "optional"],
            },
        },
        "steps": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["is_uzbek_dish", "name", "aliases", "description", "time_minutes", "ingredients", "steps"],
}

RESEARCH_SYSTEM = """Sen o'zbek milliy taomlari bo'yicha tadqiqotchisan. Foydalanuvchi so'ragan taomning an'anaviy
o'zbekcha retseptini Google qidiruvi orqali top. Bir nechta ishonchli manbani solishtirib, quyidagilarni aniqla:
taom haqiqatan o'zbek oshxonasiga tegishlimi; masalliqlar va ularning 1 kishiga to'g'ri keladigan miqdori (grammda);
tayyorlash bosqichlari; umumiy vaqt. Agar taom o'zbek oshxonasiga tegishli bo'lmasa, buni aniq ayt."""

RECIPE_SYSTEM = f"""Tadqiqot natijasini retsept JSON sxemasiga o'gir.
- Hamma matnlar o'zbek tilida (lotin yozuvi). Taom nomi o'zbekcha an'anaviy nomida.
- Taom o'zbek oshxonasiga tegishli bo'lmasa, is_uzbek_dish=false qilib, qolgan maydonlarni bo'sh qoldir.
- ingredients: grams_per_person — 1 kishi uchun grammda. Masalliq nomlari katalogda bo'lsa, AYNAN katalogdagi
  nomni ishlat (har qanday qizil go'sht uchun "go'sht"). Tuz, ziravorlar, suv, ko'katlar va bezak uchun
  masalliqlarni optional=true qil.
- steps: 4-9 ta qadam, samimiy oshpaz ohangida, qozon, zirvak, kapgir, damlash kabi milliy atamalarni ishlatib.
- aliases: taomning boshqa yozilish shakllari (apostrofsiz, kirillcha, ruscha).

Katalog:
{_CATALOG_HINT}"""


def _research(query: str) -> tuple[str, list[str]]:
    response = _generate(
        f"Taom: {query}",
        system=RESEARCH_SYSTEM,
        thinking=types.ThinkingLevel.MEDIUM,
        tools=[types.Tool(google_search=types.GoogleSearch())],
        max_output_tokens=8000,
    )
    urls: list[str] = []
    metadata = response.candidates[0].grounding_metadata
    for chunk in (metadata.grounding_chunks if metadata else None) or []:
        if chunk.web and chunk.web.uri:
            urls.append(chunk.web.uri)
    return response.text or "", list(dict.fromkeys(urls))[:8]


def research_recipe(query: str) -> dict:
    """Google qidiruvi orqali retseptni topib, RECIPE_SCHEMA ko'rinishida qaytaradi (+ "sources").

    Ikki bosqich: qidiruv bilan erkin matn, keyin JSON sxemaga o'girish — Flash modellarida
    qidiruv va sxemani bitta so'rovda birlashtirish kafolatlanmagan.
    """
    research, urls = _research(query)
    if not research.strip():
        raise LLMUnavailable("empty_research")
    response = _generate(
        f"So'rov: {query}\n\nTadqiqot natijasi:\n{research}",
        system=RECIPE_SYSTEM,
        max_output_tokens=8000,
        **_json_config(RECIPE_SCHEMA),
    )
    data = _json(response)
    data["sources"] = urls
    return data


# ---------------------------------------------------------------- suhbat


def chat(history: list[dict], context: str | None = None) -> str:
    system = PERSONA_SYSTEM
    if context:
        system += "\n\nHozirgi holat:\n" + context
    turns: list[tuple[str, str]] = []
    for msg in history[-12:]:
        role = "model" if msg.get("role") == "assistant" else "user"
        content = str(msg.get("content", "")).strip()[:2000]
        if not content:
            continue
        if turns and turns[-1][0] == role:
            turns[-1] = (role, turns[-1][1] + "\n" + content)
        else:
            turns.append((role, content))
    while turns and turns[0][0] != "user":
        turns.pop(0)
    if not turns or turns[-1][0] != "user":
        raise LLMUnavailable("empty_chat")
    contents = [types.Content(role=role, parts=[types.Part.from_text(text=text)]) for role, text in turns]
    response = _generate(contents, system=system, max_output_tokens=2000)
    return (response.text or "").strip()
