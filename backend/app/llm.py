"""Gemini API integratsiyasi: matnni masalliqlarga ajratish, yangi retseptni Google qidiruvi orqali topish, suhbat."""

import json
import logging
import time

from google import genai
from google.genai import errors, types

from .config import settings
from .ingredients import CATALOG, CATEGORIES, DEFAULT_LANG
from .persona import persona_system

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


def _models() -> list[str]:
    models = [settings.gemini_model]
    if settings.gemini_fallback_model and settings.gemini_fallback_model not in models:
        models.append(settings.gemini_fallback_model)
    return models


def _call(model: str, contents, system: str, thinking: types.ThinkingLevel, config: dict) -> types.GenerateContentResponse:
    return _get_client().models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system,
            thinking_config=types.ThinkingConfig(thinking_level=thinking),
            **config,
        ),
    )


def _generate(contents, *, system: str, thinking: types.ThinkingLevel = types.ThinkingLevel.LOW, **config) -> types.GenerateContentResponse:
    """Bepul tarifda 503 (band) va 429 (limit) tez-tez uchraydi: asosiy modelni bir marta qayta urinadi,
    keyin zaxira modelga o'tadi (bepul limitlar har bir model uchun alohida)."""
    if not enabled():
        raise LLMUnavailable("LLM o'chirilgan yoki API kalit yo'q")
    last_error = "api_error"
    response = None
    for model in _models():
        for attempt in range(2):
            try:
                response = _call(model, contents, system, thinking, config)
                break
            except errors.ClientError as e:
                if e.code == 429:
                    log.warning("Gemini %s limiti tugadi: %s", model, e.message)
                    last_error = "rate_limit"
                    break  # shu modelda qayta urinish foydasiz — zaxira modelga o'tamiz
                log.error("Gemini so'rov xatosi %s: %s", e.code, e.message)
                raise LLMUnavailable(f"api_error_{e.code}") from e
            except errors.ServerError as e:
                log.warning("Gemini %s server xatosi %s (urinish %d): %s", model, e.code, attempt + 1, e.message)
                last_error = f"server_error_{e.code}"
                time.sleep(2)
            except errors.APIError as e:
                log.error("Gemini xatosi %s: %s", e.code, e.message)
                raise LLMUnavailable("api_error") from e
            except OSError as e:
                log.error("Gemini bilan aloqa yo'q: %s", e)
                raise LLMUnavailable("connection") from e
        if response is not None:
            break
    if response is None:
        raise LLMUnavailable(last_error)

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
    f"- {i.name} (en: {i.en}; tr: {i.tr}; category: {i.category})" + (f", 1 piece ≈ {int(i.piece_g)} g" if i.piece_g else "")
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

STOCK_SYSTEM = f"""The user lists groceries they brought home, in free text. The text may be in Uzbek (Latin or
Cyrillic), English, Turkish or Russian. Extract every food product and convert its amount to GRAMS.

Rules:
- If the product is in the catalog below (in any language), set name to the catalog's canonical Uzbek name exactly
  as written (the first word(s) of the line, e.g. "piyoz" for onion / soğan).
- If it is not in the catalog, set name to the product's name in the language the user wrote in, lowercase.
- Convert pieces / bunches / heads using typical weights (use the catalog weights when given).
- Litres: water/milk ≈ 1000 g, vegetable oil ≈ 920 g.
- If no amount is given, assume a typical purchase (e.g. 1 bunch of herbs, 1 kg of a vegetable).
- Put parts that are not food or cannot be understood into "unknown", quoted as the user wrote them.

Catalog:
{_CATALOG_HINT}"""


def parse_stock(text: str) -> tuple[list[dict], list[str]]:
    response = _generate(text, system=STOCK_SYSTEM, max_output_tokens=4000, **_json_config(STOCK_SCHEMA))
    data = _json(response)
    items = [i for i in data.get("items", []) if i.get("grams", 0) > 0 and str(i.get("name", "")).strip()]
    return items, data.get("unknown", [])


# ---------------------------------------------------------------- yangi retsept (RAG)

_TRANSLATION = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "description": {"type": "string"},
        "steps": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["name", "description", "steps"],
}

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
        "translations": {
            "type": "object",
            "properties": {"en": _TRANSLATION, "tr": _TRANSLATION},
            "required": ["en", "tr"],
        },
    },
    "required": ["is_uzbek_dish", "name", "aliases", "description", "time_minutes", "ingredients", "steps", "translations"],
}

RESEARCH_SYSTEM = """You research traditional Uzbek dishes. The user names a dish (in Uzbek, English, Turkish or
Russian). Use Google Search to find its traditional Uzbek recipe. Compare several reliable sources and determine:
whether the dish really belongs to Uzbek cuisine; the ingredients and their amount per person (in grams); the cooking
steps; the total time. If the dish is not part of Uzbek cuisine, say so clearly."""

RECIPE_SYSTEM = f"""Convert the research result into the recipe JSON schema.
- name, description, steps, aliases: in Uzbek (Latin script); name is the dish's traditional Uzbek name.
- translations.en and translations.tr: the same name, description and steps in English and in Turkish, with exactly
  the same number of steps in the same order. Keep Uzbek culinary words (qozon, zirvak, kapgir...) and briefly
  explain them in the translation the first time they appear.
- If the dish is not part of Uzbek cuisine, set is_uzbek_dish=false and leave the other fields empty.
- ingredients: grams_per_person is grams for ONE person. If an ingredient is in the catalog, use the catalog's
  canonical Uzbek name exactly (use "go'sht" for any red meat). Mark salt, spices, water, herbs and garnish as
  optional=true.
- steps: 4-9 steps in the warm voice of a friendly home cook.
- aliases: other spellings of the dish (without apostrophes, Cyrillic, Russian, English, Turkish).

Catalog:
{_CATALOG_HINT}"""


def _research(query: str) -> tuple[str, list[str]]:
    response = _generate(
        f"Dish: {query}",
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
    """Google qidiruvi orqali retseptni topib, RECIPE_SCHEMA ko'rinishida (uch tilda) qaytaradi (+ "sources").

    Ikki bosqich: qidiruv bilan erkin matn, keyin JSON sxemaga o'girish — Flash modellarida
    qidiruv va sxemani bitta so'rovda birlashtirish kafolatlanmagan.
    """
    research, urls = _research(query)
    if not research.strip():
        raise LLMUnavailable("empty_research")
    response = _generate(
        f"Request: {query}\n\nResearch result:\n{research}",
        system=RECIPE_SYSTEM,
        max_output_tokens=16000,
        **_json_config(RECIPE_SCHEMA),
    )
    data = _json(response)
    data["sources"] = urls
    return data


# ---------------------------------------------------------------- suhbat


def chat(history: list[dict], context: str | None = None, lang: str = DEFAULT_LANG) -> str:
    system = persona_system(lang)
    if context:
        system += "\n\nCurrent situation:\n" + context
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
