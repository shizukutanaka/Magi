"""Deterministic topic classification for the user's question."""

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
        "恋愛",
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
        "invest",
        "debt",
        "salary",
        "budget",
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
    ),
    "decision": (
        "決断",
        "選択",
        "どちら",
        "迷",
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
    ),
    "general": (),
}


def classify_question(question: str | None) -> str | None:
    """Return the topic with the most keyword matches in a question."""
    normalized = normalize_question(question)
    if not normalized:
        return None

    scores: list[tuple[int, int, int, str]] = []
    for topic_index, topic in enumerate(TOPICS):
        matches = [
            normalized.find(keyword)
            for keyword in KEYWORDS[topic]
            if normalized.find(keyword) >= 0
        ]
        scores.append(
            (
                sum(normalized.count(keyword) for keyword in KEYWORDS[topic]),
                min(matches, default=len(normalized) + 1),
                topic_index,
                topic,
            )
        )
    best_score = max(score[0] for score in scores)
    if best_score == 0:
        return "general"
    return min(
        (score for score in scores if score[0] == best_score),
        key=lambda score: (score[1], score[2]),
    )[3]
