"""Deterministic topic classification for the user's question."""

import re

from app.divination.seed import normalize_question

TOPICS: tuple[str, ...] = (
    "love",
    "work",
    "money",
    "health",
    "relationship",
    "decision",
    "general",
)

KEYWORDS: dict[str, tuple[str, ...]] = {
    "love": (
        "恋",
        "好き",
        "片思い",
        "交際",
        "結婚",
        "復縁",
        "彼氏",
        "彼女",
        "パートナー",
        "デート",
        "love",
        "romance",
        "dating",
        "marriage",
        "partner",
        "crush",
        "boyfriend",
        "girlfriend",
        "loves",
        "loved",
        "loving",
        "lover",
        "lovers",
        "crushes",
        "crushed",
        "crushing",
        "partners",
        "marriages",
        "romances",
        "boyfriends",
        "girlfriends",
        "dates",
        "breakup",
        "breakups",
        "divorce",
        "divorced",
        "wedding",
        "weddings",
        "engaged",
        "engagement",
        "heartbreak",
        "heartbroken",
        "lovesick",
    ),
    "work": (
        "仕事",
        "転職",
        "就職",
        "職場",
        "上司",
        "部下",
        "昇進",
        "起業",
        "事業",
        "キャリア",
        "面接",
        "副業",
        "work",
        "job",
        "career",
        "boss",
        "promotion",
        "interview",
        "business",
        "startup",
        "jobs",
        "works",
        "worked",
        "working",
        "worker",
        "workers",
        "bosses",
        "interviews",
        "promotions",
        "businesses",
        "startups",
        "careers",
        "jobless",
        "workplace",
        "unemployed",
        "unemployment",
        "fired",
        "layoff",
        "layoffs",
        "laid off",
    ),
    "money": (
        "お金",
        "金銭",
        "収入",
        "貯金",
        "投資",
        "借金",
        "支出",
        "家計",
        "給料",
        "money",
        "finance",
        "income",
        "savings",
        "investment",
        "investing",
        "investor",
        "debt",
        "salary",
        "budget",
        "finances",
        "incomes",
        "investments",
        "investors",
        "debts",
        "salaries",
        "budgets",
        "bonus",
        "bonuses",
        "rent",
        "bill",
        "bills",
    ),
    "health": (
        "健康",
        "体調",
        "病気",
        "治療",
        "睡眠",
        "疲れ",
        "ストレス",
        "食事",
        "運動",
        "health",
        "illness",
        "sleep",
        "tired",
        "stress",
        "diet",
        "exercise",
        "recovery",
        "sleeps",
        "sleeping",
        "sleepless",
        "sleepy",
        "stressed",
        "stressful",
        "stresses",
        "diets",
        "dieting",
        "exercises",
        "exercised",
        "exercising",
        "illnesses",
        "recover",
        "recovered",
        "recovering",
        "recoveries",
        "workout",
        "workouts",
        "healthcare",
        "pregnant",
        "pregnancy",
        "disease",
        "diseases",
    ),
    "relationship": (
        "人間関係",
        "友人",
        "友達",
        "家族",
        "同僚",
        "近所",
        "仲直り",
        "friend",
        "family",
        "parent",
        "colleague",
        "neighbor",
        "conflict",
        "friends",
        "friendship",
        "families",
        "parents",
        "colleagues",
        "neighbors",
        "conflicts",
        "coworker",
        "coworkers",
        "argument",
        "arguments",
        "argue",
        "argued",
        "arguing",
        "betrayal",
        "betrayed",
    ),
    "decision": (
        "決断",
        "選択",
        "どちら",
        # 日本語は部分一致のため、迷信・迷子・迷路・迷惑に当たらない語幹を使う。
        "迷う",
        "迷っ",
        "迷わ",
        "迷い",
        "決め",
        "進むべき",
        "やめるべき",
        "引っ越し",
        "decide",
        "decision",
        "choose",
        "choice",
        "whether",
        "should i",
        "move",
        "decides",
        "decided",
        "deciding",
        "decisions",
        "chooses",
        "chose",
        "choosing",
        "choices",
        "moves",
        "moved",
        "moving",
    ),
}

# 英語キーワードは左右とも語境界を要求する。活用形（moving・jobs・sleepless
# 等）は正規表現の接尾辞ではなく KEYWORDS に明示する。—lovely→恋愛、
# movement→決断 のような別語への誤爆を防ぐため、語の途中で切れない。
_ASCII_PATTERNS: dict[str, dict[str, re.Pattern[str]]] = {
    topic: {
        keyword: re.compile(r"(?<![a-z0-9])" + re.escape(keyword) + r"(?![a-z0-9])")
        for keyword in keywords
        if keyword.isascii()
    }
    for topic, keywords in KEYWORDS.items()
}


def classify_question(question: str | None) -> str | None:
    """Return the topic with the most keyword matches in a question."""
    normalized = normalize_question(question)
    if not normalized:
        return None

    ranked: list[tuple[int, int, int, str]] = []
    for topic_index, topic in enumerate(TOPICS):
        if topic not in KEYWORDS:
            continue
        count = 0
        earliest = len(normalized)
        ascii_patterns = _ASCII_PATTERNS[topic]
        for keyword in KEYWORDS[topic]:
            pattern = ascii_patterns.get(keyword)
            if pattern is not None:
                matches = list(pattern.finditer(normalized))
                if matches:
                    count += len(matches)
                    earliest = min(earliest, matches[0].start())
            else:
                index = normalized.find(keyword)
                if index >= 0:
                    count += normalized.count(keyword)
                    earliest = min(earliest, index)
        if count:
            ranked.append((-count, earliest, topic_index, topic))
    if not ranked:
        return "general"
    return min(ranked)[3]
