"""Small helpers shared by engine implementations."""

from datetime import UTC, datetime

from app.divination.base import DrawnSymbol, LuckyItems, Reading, ReadingSection
from app.divination.interpretation import interpretation_langs
from app.divination.seed import SeededRandom
from app.i18n import DEFAULT_LANG, Lang, t


def first_sentence(text: str) -> str:
    for terminator in ("。", ". "):
        head, separator, _ = text.partition(terminator)
        if separator:
            return head
    return text.removesuffix(".")


def finish(
    engine_id: str,
    engine_name: str,
    tradition: str,
    seed: str,
    drawn: list[DrawnSymbol],
    summary: str,
    sections: list[ReadingSection],
    score: int,
    rng: SeededRandom,
    lang: Lang = "ja",
) -> Reading:
    colors = ["indigo", "gold", "young_green", "vermilion", "white"]
    directions = ["east", "west", "south", "north"]
    items = ["notebook", "teacup", "key", "plant", "clock"]
    supported = interpretation_langs(engine_id)
    interpretation_lang = lang if lang in supported else DEFAULT_LANG
    return Reading(
        engine_id=engine_id,
        engine_name=engine_name,
        tradition=tradition,
        seed=seed,
        drawn=drawn,
        summary=summary,
        sections=sections,
        score=max(0, min(100, score)),
        lucky=LuckyItems(
            color=t(lang, f"lucky.color.{rng.choice(colors)}"),
            number=rng.randint(1, 9),
            direction=t(lang, f"lucky.direction.{rng.choice(directions)}"),
            item=t(lang, f"lucky.item.{rng.choice(items)}"),
        ),
        generated_at=datetime.now(UTC),
        disclaimer=t(lang, "disclaimer"),
        lang=lang,
        interpretation_lang=interpretation_lang,
    )
