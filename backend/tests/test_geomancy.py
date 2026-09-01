from datetime import date

from fastapi.testclient import TestClient

from app.divination.base import DivinationInput
from app.divination.data.geomancy import FIGURES, FIGURES_BY_LINES
from app.divination.engines.geomancy import GeomancyEngine, add_figures, build_shield
from app.divination.seed import SeededRandom, build_seed
from app.main import app

client = TestClient(app)


class FixedRng:
    def __init__(self, values: list[int]) -> None:
        self.values = iter(values)

    def randint(self, start: int, end: int) -> int:
        assert (start, end) == (1, 16)
        return next(self.values)


def test_all_figure_patterns_are_present_once():
    assert len(FIGURES) == 16
    assert len({figure.lines for figure in FIGURES}) == 16
    assert all(line in (1, 2) for figure in FIGURES for line in figure.lines)


def test_parity_addition():
    via = FIGURES_BY_LINES[(1, 1, 1, 1)]
    populus = FIGURES_BY_LINES[(2, 2, 2, 2)]
    puer = FIGURES_BY_LINES[(1, 1, 2, 1)]
    assert add_figures(via, via) == populus
    assert add_figures(puer, populus) == puer
    assert all(add_figures(figure, figure) == populus for figure in FIGURES)


def test_daughters_are_the_transpose_of_explicit_mothers():
    mother_lines = (
        (1, 1, 1, 1),
        (1, 1, 2, 1),
        (1, 2, 1, 1),
        (2, 2, 2, 2),
    )
    values = [1 if line == 1 else 2 for lines in mother_lines for line in lines]
    chart = build_shield(FixedRng(values))
    mothers = tuple(FIGURES_BY_LINES[lines] for lines in mother_lines)
    expected_daughters = tuple(
        FIGURES_BY_LINES[tuple(mother.lines[index] for mother in mothers)]
        for index in range(4)
    )
    assert chart.mothers == mothers
    assert chart.daughters == expected_daughters


def test_geomancy_is_deterministic_and_subject_derived():
    engine = GeomancyEngine()
    inp = DivinationInput(target_date=date(2026, 9, 1))
    first_seed = build_seed("same", engine.id, inp)
    first = engine.cast(inp, SeededRandom(first_seed))
    second = engine.cast(inp, SeededRandom(first_seed))
    other_seed = build_seed("other", engine.id, inp)
    assert first.seed == second.seed == first_seed
    assert first.drawn == second.drawn
    assert other_seed != first_seed


def test_judge_is_derived_from_the_shield():
    inp = DivinationInput(target_date=date(2026, 9, 1))
    seed = build_seed("shield", "geomancy", inp)
    chart = build_shield(SeededRandom(seed))
    right = add_figures(chart.nieces[0], chart.nieces[1])
    left = add_figures(chart.nieces[2], chart.nieces[3])
    judge = add_figures(right, left)
    assert chart.right_witness == right
    assert chart.left_witness == left
    assert chart.judge == judge


def test_geomancy_text_integrity():
    texts = [getattr(figure, field) for figure in FIGURES for field in ("judgment", "witness", "practice")]
    assert len(texts) == 48
    assert len(set(texts)) == 48
    assert all(40 <= len(text) <= 90 for text in texts)
    assert all(figure.name not in getattr(figure, field) for figure in FIGURES for field in ("judgment", "witness", "practice"))
    assert all(0 <= figure.base_score <= 100 for figure in FIGURES)


def test_geomancy_is_registered_in_api():
    systems = client.get("/api/v1/systems")
    assert systems.status_code == 200
    assert any(system["id"] == "geomancy" for system in systems.json())
    response = client.post(
        "/api/v1/readings",
        json={"engine_id": "geomancy", "input": {"target_date": "2026-09-01"}},
    )
    assert response.status_code == 200
    assert [symbol["position"] for symbol in response.json()["drawn"]] == ["右証人", "左証人", "判事"]
