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
    culture = "western"
    required_fields = frozenset()
    default_options = {"spread": "three-card"}

    def cast(self, inp: DivinationInput, rng: SeededRandom, lang: Lang = "ja"):
        spread = inp.options.get("spread", "three-card")
        if spread not in ALLOWED_SPREADS:
            raise ValueError(f"unknown tarot spread: {spread}")
        positions = (
            t(lang, "position.tarot.past"), t(lang, "position.tarot.present"), t(lang, "position.tarot.future")
        ) if spread == "three-card" else (
            t(lang, "position.tarot.current"), t(lang, "position.tarot.challenge"), t(lang, "position.tarot.past"), t(lang, "position.tarot.near_future"),
            t(lang, "position.tarot.conscious"), t(lang, "position.tarot.unconscious"), t(lang, "position.tarot.self"), t(lang, "position.tarot.environment"),
            t(lang, "position.tarot.hope"), t(lang, "position.tarot.conclusion"),
        )
        cards = rng.sample(CARDS, len(positions))
        drawn = []
        for card, position in zip(cards, positions, strict=True):
            reversed_card = bool(rng.randint(0, 1))
            drawn.append(
                DrawnSymbol(
                    key=card.key,
                    name=dt(lang, self.id, f"{card.key}.name", card.name_ja),
                    position=position,
                    reversed=reversed_card,
                )
            )
        lead = cards[0]
        lead_meaning_key = "reversed_meaning" if drawn[0].reversed else "upright_meaning"
        lead_meaning_source = (
            lead.reversed_meaning if drawn[0].reversed else lead.upright_meaning
        )
        lead_meaning = dt(
            lang,
            self.id,
            f"{lead.key}.{lead_meaning_key}",
            lead_meaning_source,
        )
        lead_name = dt(lang, self.id, f"{lead.key}.name", lead.name_ja)
        sections = [
            ReadingSection(
                title=symbol.position,
                body=dt(
                    lang,
                    self.id,
                    f"{card.key}.reversed_meaning"
                    if symbol.reversed
                    else f"{card.key}.upright_meaning",
                    card.reversed_meaning if symbol.reversed else card.upright_meaning,
                ),
            )
            for card, symbol in zip(cards, drawn, strict=True)
        ]
        sections.append(
            ReadingSection(title=t(lang, "section.guidance"), body=t(lang, "body.tarot.guidance"))
        )
        return finish(
            self.id, t(lang, "engine.tarot.name"), t(lang, "engine.tarot.tradition"), rng.seed, drawn,
            t(lang, "summary.tarot", name=lead_name, meaning=first_sentence(lead_meaning)),
            sections,
            None, rng, lang,
        )


engine: DivinationEngine = register(TarotEngine())
