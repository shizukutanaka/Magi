"""Rider-Waite-Smith tarot engine."""

from app.divination.base import DivinationEngine, DivinationInput, DrawnSymbol, ReadingSection
from app.divination.data.localize import dt
from app.divination.data.tarot import CARDS
from app.divination.engines._common import finish, first_sentence
from app.divination.registry import register
from app.divination.seed import SeededRandom
from app.i18n import Lang, t

ALLOWED_SPREADS = ("three-card", "celtic-cross")


class TarotEngine:
    id = "tarot"
    name = "タロット"
    tradition = "西洋"
    required_fields = frozenset()
    default_options = {"spread": "three-card"}

    def cast(self, inp: DivinationInput, rng: SeededRandom, lang: Lang = "ja"):
        spread = inp.options.get("spread", "three-card")
        if spread not in ALLOWED_SPREADS:
            raise ValueError(f"unknown tarot spread: {spread}")
        positions = (
            (t(lang, "position.tarot.past"), "present"), (t(lang, "position.tarot.present"), "present"), (t(lang, "position.tarot.future"), "present")
        ) if spread == "three-card" else (
            (t(lang, "position.tarot.current"), "present"), (t(lang, "position.tarot.challenge"), "present"), (t(lang, "position.tarot.past"), "present"), (t(lang, "position.tarot.near_future"), "present"),
            (t(lang, "position.tarot.conscious"), "present"), (t(lang, "position.tarot.unconscious"), "present"), (t(lang, "position.tarot.self"), "present"), (t(lang, "position.tarot.environment"), "present"),
            (t(lang, "position.tarot.hope"), "present"), (t(lang, "position.tarot.conclusion"), "present"),
        )
        cards = rng.sample(CARDS, len(positions))
        drawn = []
        for card, (position, _) in zip(cards, positions, strict=True):
            reversed_card = bool(rng.randint(0, 1))
            drawn.append(
                DrawnSymbol(
                    key=card.key,
                    name=dt(lang, self.id, f"{card.key}.name", card.name_ja),
                    position=position,
                    reversed=reversed_card,
                    image_hint=f"tarot/{card.key}",
                )
            )
        lead = cards[0]
        meaning_key = "reversed_meaning" if drawn[0].reversed else "upright_meaning"
        meaning_source = (
            lead.reversed_meaning if drawn[0].reversed else lead.upright_meaning
        )
        meaning = dt(lang, self.id, f"{lead.key}.{meaning_key}", meaning_source)
        lead_name = dt(lang, self.id, f"{lead.key}.name", lead.name_ja)
        return finish(
            self.id, t(lang, "engine.tarot.name"), t(lang, "engine.tarot.tradition"), rng.seed, drawn,
            t(lang, "summary.tarot", name=lead_name, meaning=first_sentence(meaning)),
            [
                ReadingSection(title=t(lang, "section.overall"), body=meaning),
                ReadingSection(title=t(lang, "section.love"), body=t(lang, "body.tarot.love")),
                ReadingSection(title=t(lang, "section.work"), body=t(lang, "body.tarot.work")),
                ReadingSection(title=t(lang, "section.finance"), body=t(lang, "body.tarot.finance")),
                ReadingSection(title=t(lang, "section.guidance"), body=t(lang, "body.tarot.guidance")),
            ],
            rng.randint(45, 95), rng, lang,
        )


engine: DivinationEngine = register(TarotEngine())
