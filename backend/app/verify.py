"""Offline share-URL verification CLI."""

import argparse
import json
import sys
from datetime import date, time
from urllib.parse import parse_qs, urlparse

from pydantic import ValidationError

from app.divination.base import DivinationInput, Reading
from app.divination.registry import UnknownEngineError
from app.divination.service import (
    MissingFieldsError,
    UnknownSpreadError,
    cast_reading,
    daily_reading,
)
from app.i18n import resolve_lang


def _query_values(share_url: str) -> dict[str, str]:
    parsed = urlparse(share_url)
    query = parsed.query
    if not query and "=" in parsed.path:
        query = parsed.path.lstrip("?")
    return {key: values[0] for key, values in parse_qs(query, keep_blank_values=True).items()}


def _input_from_query(params: dict[str, str]) -> DivinationInput:
    try:
        options = {"spread": params["spread"]} if params.get("spread") else {}
        return DivinationInput(
            target_date=date.fromisoformat(params.get("date") or date.today().isoformat()),
            question=params.get("q") or None,
            birth_date=date.fromisoformat(params["birth"]) if params.get("birth") else None,
            birth_time=time.fromisoformat(params["time"]) if params.get("time") else None,
            full_name=params.get("name") or None,
            options=options,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("共有URLの日付または時刻を解釈できません。") from exc


def _readings_from_result(result: dict | Reading) -> list[Reading]:
    return [result] if isinstance(result, Reading) else result["readings"]


def _print_reading(reading: Reading) -> None:
    print(f"流派: {reading.engine_name}（{reading.tradition}）")
    print(f"シード: {reading.seed}")
    print("象徴:")
    for symbol in reading.drawn:
        reversed_marker = "（逆位置）" if symbol.reversed else ""
        print(f"  {symbol.key} / {symbol.name} / {symbol.position}{reversed_marker}")
    print(f"要約: {reading.summary}")
    if reading.score is not None:
        print(f"スコア: {reading.score}")


def _print_human(result: dict) -> None:
    readings = _readings_from_result(result)
    if len(readings) > 1:
        print("今日の三賢者")
    for index, reading in enumerate(readings):
        if index:
            print()
        _print_reading(reading)
    if len(readings) > 1:
        print(f"概要: {result['overview']}")
        print(f"平均スコア: {result['score']}" if result["score"] is not None else "平均スコア: なし")


def _print_json(result: dict | Reading) -> None:
    if isinstance(result, Reading):
        payload = result.model_dump(mode="json")
    else:
        payload = dict(result)
        payload["readings"] = [reading.model_dump(mode="json") for reading in _readings_from_result(result)]
    print(json.dumps(payload, ensure_ascii=False))


def _print_seed_check(expected: str, readings: list[Reading], as_json: bool) -> bool:
    matched = any(reading.seed == expected for reading in readings)
    message = f"シード: {'一致' if matched else '不一致'}（期待値: {expected}）"
    print(message, file=sys.stderr if as_json else sys.stdout)
    return matched


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Magiの共有URLをオフラインで検証します。")
    parser.add_argument("share_url", help="Magiの共有URLまたはクエリ文字列")
    parser.add_argument("--expect-seed", dest="expected_seed")
    parser.add_argument("--lang", choices=("ja", "en"))
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)

    try:
        params = _query_values(args.share_url)
        inp = _input_from_query(params)
        subject_key = params.get("s") or "anonymous"
        lang = resolve_lang(args.lang or params.get("lang"), None)
        if params.get("daily") == "1":
            result = daily_reading(inp, subject_key, lang)
        else:
            engine_id = params.get("engine")
            if not engine_id:
                raise ValueError("共有URLにengineが指定されていません。")
            result = cast_reading(engine_id, inp, subject_key, lang)
    except UnknownEngineError:
        print(f"未知の流派です: {params.get('engine', '')}", file=sys.stderr)
        return 2
    except MissingFieldsError as exc:
        labels = {
            "birth_date": "生年月日",
            "birth_time": "出生時刻",
            "full_name": "氏名",
            "question": "問い",
        }
        print(f"必須入力が不足しています: {', '.join(labels.get(field, field) for field in exc.fields)}", file=sys.stderr)
        return 2
    except UnknownSpreadError:
        print("未知のスプレッドです。", file=sys.stderr)
        return 2
    except (ValidationError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    readings = _readings_from_result(result)
    if args.as_json:
        _print_json(result)
    else:
        _print_human(result)
    if args.expected_seed is not None and not _print_seed_check(args.expected_seed, readings, args.as_json):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
