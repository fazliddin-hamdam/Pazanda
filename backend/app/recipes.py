"""Retseptlar bazasi: qidirish, saqlash va topilmasa Gemini orqali yangi retsept olish (RAG)."""

import difflib
import logging
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import llm
from .ingredients import canonical, normalize
from .models import Recipe
from .seed_recipes import SEED_RECIPES

log = logging.getLogger(__name__)


class RecipeNotFound(Exception):
    pass


class NotUzbekDish(Exception):
    pass


def _key(text: str) -> str:
    return re.sub(r"[^a-z0-9а-яёўқғҳ ]", "", normalize(text)).replace(" ", "")


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", normalize(text).replace("'", "")).strip("-") or "taom"


def seed(db: Session) -> None:
    existing = set(db.scalars(select(Recipe.slug)).all())
    for data in SEED_RECIPES:
        if data["slug"] not in existing:
            db.add(Recipe(source="seed", **data))
    db.commit()


def all_recipes(db: Session) -> list[Recipe]:
    return list(db.scalars(select(Recipe).order_by(Recipe.name)).all())


def find(db: Session, query: str) -> Recipe | None:
    """Nom yoki muqobil nomlar bo'yicha (apostrof, bo'shliq va kichik xatolarga chidamli) qidirish."""
    q = _key(query)
    if not q:
        return None
    recipes = all_recipes(db)
    names: dict[str, Recipe] = {}
    for r in recipes:
        for n in (r.name, r.slug, *(r.aliases or [])):
            names[_key(n)] = r
    if q in names:
        return names[q]
    close = difflib.get_close_matches(q, names.keys(), n=1, cutoff=0.82)
    return names[close[0]] if close else None


def get(db: Session, slug: str) -> Recipe | None:
    return db.scalar(select(Recipe).where(Recipe.slug == slug))


def _clean_ingredients(items: list[dict]) -> list[dict]:
    cleaned = []
    for item in items:
        grams = float(item.get("grams_per_person", 0))
        name = str(item.get("name", "")).strip()
        if not name or grams <= 0:
            continue
        cleaned.append({"name": canonical(name)[0], "grams_per_person": round(grams, 1), "optional": bool(item.get("optional"))})
    return cleaned


def upsert(db: Session, data: dict, source: str) -> Recipe:
    """JSON retseptni saqlaydi (n8n workflow yoki Gemini natijasi)."""
    ingredients = _clean_ingredients(data.get("ingredients", []))
    steps = [s.strip() for s in data.get("steps", []) if str(s).strip()]
    if not data.get("name") or not ingredients or not steps:
        raise ValueError("retseptda nom, masalliqlar yoki qadamlar yo'q")
    slug = data.get("slug") or slugify(data["name"])
    recipe = get(db, slug) or Recipe(slug=slug)
    recipe.name = data["name"].strip()
    recipe.aliases = sorted({a.strip() for a in data.get("aliases", []) if a.strip()})
    recipe.description = data.get("description", "")
    recipe.time_minutes = int(data.get("time_minutes") or 60)
    recipe.ingredients = ingredients
    recipe.steps = steps
    recipe.source = source
    recipe.sources = data.get("sources", [])
    db.add(recipe)
    db.commit()
    return recipe


def resolve(db: Session, query: str) -> Recipe:
    """Bazadan qidiradi; topilmasa Gemini Google qidiruvi bilan topib, bazaga saqlaydi."""
    recipe = find(db, query)
    if recipe:
        return recipe
    if not llm.enabled():
        raise llm.LLMUnavailable("disabled")
    data = llm.research_recipe(query)
    if not data.get("is_uzbek_dish"):
        raise NotUzbekDish(query)
    # Model kanonik nomni qaytargan bo'lishi mumkin, u esa bazada bor bo'lishi mumkin
    existing = find(db, data.get("name", ""))
    if existing:
        return existing
    data.setdefault("aliases", []).append(query)
    try:
        recipe = upsert(db, data, source="ai")
    except ValueError as e:
        log.warning("AI retsepti yaroqsiz (%s): %s", query, e)
        raise RecipeNotFound(query) from e
    log.info("Yangi retsept saqlandi: %s", recipe.slug)
    return recipe
