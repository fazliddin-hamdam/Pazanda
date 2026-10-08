"""Ombor tahlili: retseptga yetadimi, nima yetishmaydi, qaysi taomni tavsiya qilish, taomdan keyin ayirish."""

from dataclasses import asdict, dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from .ingredients import SUBSTITUTES, canonical, is_staple
from .models import Recipe, StockItem

# Shuncha grammdan kam yetishmovchilik e'tiborga olinmaydi
TOLERANCE_G = 5


@dataclass
class IngredientCheck:
    name: str
    need_g: float
    have_g: float
    missing_g: float
    optional: bool
    staple: bool


@dataclass
class RecipeCheck:
    slug: str
    name: str
    servings: int
    coverage: float  # 0..1, majburiy masalliqlar bo'yicha
    ingredients: list[IngredientCheck]

    @property
    def missing(self) -> list[IngredientCheck]:
        return [i for i in self.ingredients if not i.optional and not i.staple and i.missing_g > TOLERANCE_G]

    @property
    def ready(self) -> bool:
        return not self.missing

    def to_dict(self) -> dict:
        data = asdict(self)
        data["missing"] = [asdict(i) for i in self.missing]
        data["ready"] = self.ready
        return data


def stock_map(db: Session, user_id: int) -> dict[str, float]:
    rows = db.scalars(select(StockItem).where(StockItem.user_id == user_id)).all()
    return {r.name: r.grams for r in rows if r.grams > 0}


def _sources(name: str) -> list[str]:
    return SUBSTITUTES.get(name, [name])


def available(stock: dict[str, float], name: str) -> float:
    return sum(stock.get(n, 0) for n in _sources(name))


def check_recipe(recipe: Recipe, servings: int, stock: dict[str, float]) -> RecipeCheck:
    checks: list[IngredientCheck] = []
    ratios: list[float] = []
    for item in recipe.ingredients:
        name = canonical(item["name"])[0]
        need = float(item["grams_per_person"]) * servings
        have = available(stock, name)
        staple = is_staple(name)
        optional = bool(item.get("optional"))
        checks.append(IngredientCheck(name, need, have, max(0.0, need - have), optional, staple))
        if not optional and not staple and need > 0:
            ratios.append(min(1.0, have / need))
    coverage = sum(ratios) / len(ratios) if ratios else 1.0
    return RecipeCheck(recipe.slug, recipe.name, servings, round(coverage, 3), checks)


def suggest(recipes: list[Recipe], servings: int, stock: dict[str, float], limit: int = 3) -> list[RecipeCheck]:
    """Ombordagi masalliqlarga eng mos keladigan taomlar: avval to'liq yetadiganlari, keyin eng yaqinlari."""
    checks = [check_recipe(r, servings, stock) for r in recipes]
    checks = [c for c in checks if c.coverage > 0]
    checks.sort(key=lambda c: (c.ready, c.coverage, -len(c.missing)), reverse=True)
    return checks[:limit]


def consume(db: Session, user_id: int, recipe: Recipe, servings: int) -> list[dict]:
    """Taom tayyor bo'lgach ishlatilgan masalliqlarni ombordan ayiradi. Ayirilganlar ro'yxatini qaytaradi."""
    rows = {r.name: r for r in db.scalars(select(StockItem).where(StockItem.user_id == user_id)).all()}
    used: list[dict] = []
    for item in recipe.ingredients:
        name = canonical(item["name"])[0]
        if is_staple(name):
            continue
        remaining = float(item["grams_per_person"]) * servings
        taken = 0.0
        for source in _sources(name):
            row = rows.get(source)
            if not row or row.grams <= 0 or remaining <= 0:
                continue
            take = min(row.grams, remaining)
            row.grams -= take
            remaining -= take
            taken += take
            if row.grams < 1:
                db.delete(row)
        if taken > 0:
            used.append({"name": name, "grams": round(taken)})
    db.flush()
    return used
