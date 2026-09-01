"""Small helpers shared by engine implementations."""

from datetime import UTC, datetime

from app.divination.base import DISCLAIMER, DrawnSymbol, LuckyItems, Reading, ReadingSection
from app.divination.seed import SeededRandom


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
) -> Reading:
    if drawn:
        first = drawn[0]
        drawn[0] = first.model_copy(update={"image_hint": f"{first.image_hint or engine_id}/{seed[:12]}"})
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
            color=rng.choice(["藍色", "金色", "若草色", "朱色", "白色"]),
            number=rng.randint(1, 9),
            direction=rng.choice(["東", "西", "南", "北"]),
            item=rng.choice(["ノート", "湯のみ", "鍵", "植物", "時計"]),
        ),
        generated_at=datetime.now(UTC),
        disclaimer=DISCLAIMER,
    )
