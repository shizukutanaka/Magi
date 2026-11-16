// 占い結果を1枚の画像（カード）にして共有／保存するためのモジュール。
// 画像生成は Canvas のみで端末内で完結し、外部送信は一切しない。
// 共有は Web Share API（ファイル共有）を使い、使えない環境では
// PNG のダウンロードにフォールバックする。

export const CARD_WIDTH = 1200;
export const CARD_HEIGHT = 630;

const PADDING = 64;
const CONTENT_WIDTH = CARD_WIDTH - PADDING * 2;
const FOOTER_LINE_Y = CARD_HEIGHT - 64;
const FOOTER_TEXT_Y = CARD_HEIGHT - 28;

// styles.css の配色に合わせる。
const COLORS = {
  paper: "#fcfaf7",
  ink: "#28232f",
  muted: "#716979",
  accent: "#8a4e68",
  line: "#e8e0d8",
};
const FONT_FAMILY = 'ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif';

// reading からカードに載せる内容を取り出す。描画と分離してあるので、
// Canvas がない環境でも内容の組み立てだけを検証できる。
export function buildCardContent(reading) {
  const drawn = (reading.drawn || []).map((symbol) => ({
    name: String(symbol.name ?? ""),
    position: String(symbol.position ?? ""),
    reversed: Boolean(symbol.reversed),
  }));
  const lucky = reading.lucky
    ? {
        color: String(reading.lucky.color ?? ""),
        number: String(reading.lucky.number ?? ""),
        direction: String(reading.lucky.direction ?? ""),
        item: String(reading.lucky.item ?? ""),
      }
    : null;
  return {
    title: String(reading.engine_name ?? ""),
    tradition: String(reading.tradition ?? ""),
    summary: String(reading.summary ?? ""),
    drawn,
    score: reading.score === null || reading.score === undefined ? null : reading.score,
    lucky,
  };
}

// 描画用の1行文字列にする。逆位置は表示名に印を付ける。
export function drawnLine(symbol, labels) {
  const name = `${symbol.name}${symbol.reversed ? labels.reversed : ""}`;
  return symbol.position ? `${name} — ${symbol.position}` : name;
}

export function luckyLine(lucky, labels) {
  const parts = [
    `${labels.color}: ${lucky.color}`,
    `${labels.number}: ${lucky.number}`,
    `${labels.direction}: ${lucky.direction}`,
    `${labels.item}: ${lucky.item}`,
  ];
  return `${labels.lucky}: ${parts.join(" / ")}`;
}

// measure(text) が描画幅を返す前提で、maxWidth に収まるよう折り返す。
// 空白で区切れる単語は単語の途中で割らない。空白のない長い文字列
// （日本語など）は文字単位で割る。maxLines を超える分は末尾を「…」で省略する。
export function wrapText(text, maxWidth, measure, maxLines = Infinity) {
  const lines = [];
  for (const paragraph of String(text ?? "").split("\n")) {
    let line = "";
    let lastBreak = -1; // line 内で直近に確認した空白の位置
    for (const char of paragraph) {
      const candidate = line + char;
      if (line && measure(candidate) > maxWidth) {
        if (char === " ") {
          lines.push(line);
          line = "";
          lastBreak = -1;
          continue;
        }
        if (lastBreak > 0) {
          lines.push(line.slice(0, lastBreak));
          line = line.slice(lastBreak + 1) + char;
          lastBreak = -1;
          continue;
        }
        lines.push(line);
        line = char;
        lastBreak = -1;
        continue;
      }
      line = candidate;
      if (char === " ") lastBreak = line.length - 1;
    }
    lines.push(line);
  }
  if (lines.length > maxLines) {
    const kept = lines.slice(0, maxLines);
    const chars = [...kept[kept.length - 1]];
    while (chars.length && measure(`${chars.join("")}…`) > maxWidth) chars.pop();
    kept[kept.length - 1] = `${chars.join("")}…`;
    return kept;
  }
  return lines;
}

function setFont(ctx, size, weight = 400) {
  ctx.font = `${weight} ${size}px ${FONT_FAMILY}`;
  return (text) => ctx.measureText(text).width;
}

// カードを Canvas に描く。createCanvas はテスト用の差し替え口で、
// 既定では通常の canvas 要素を作る。
export function renderCardImage(reading, labels, createCanvas = () => document.createElement("canvas")) {
  const content = buildCardContent(reading);
  const canvas = createCanvas();
  canvas.width = CARD_WIDTH;
  canvas.height = CARD_HEIGHT;
  const ctx = canvas.getContext("2d");

  ctx.fillStyle = COLORS.paper;
  ctx.fillRect(0, 0, CARD_WIDTH, CARD_HEIGHT);
  ctx.textBaseline = "alphabetic";

  let y = 96;
  ctx.fillStyle = COLORS.ink;
  let measure = setFont(ctx, 54, 700);
  ctx.fillText(wrapText(content.title, CONTENT_WIDTH, measure, 1)[0] ?? "", PADDING, y);

  y += 44;
  ctx.fillStyle = COLORS.muted;
  measure = setFont(ctx, 27);
  ctx.fillText(wrapText(content.tradition, CONTENT_WIDTH, measure, 1)[0] ?? "", PADDING, y);

  y += 26;
  ctx.fillStyle = COLORS.accent;
  ctx.fillRect(PADDING, y, CONTENT_WIDTH, 3);

  // 要約
  y += 58;
  ctx.fillStyle = COLORS.ink;
  measure = setFont(ctx, 30);
  for (const line of wrapText(content.summary, CONTENT_WIDTH, measure, 3)) {
    ctx.fillText(line, PADDING, y);
    y += 44;
  }

  // 引いた象徴は1段落に流し込む（数が多いスプレッドでも収まるように）
  if (content.drawn.length) {
    y += 8;
    ctx.fillStyle = COLORS.ink;
    measure = setFont(ctx, 25);
    const joined = content.drawn.map((symbol) => drawnLine(symbol, labels)).join(" ・ ");
    for (const line of wrapText(joined, CONTENT_WIDTH, measure, 3)) {
      ctx.fillText(line, PADDING, y);
      y += 38;
    }
  }

  if (content.score !== null) {
    y += 10;
    ctx.fillStyle = COLORS.ink;
    measure = setFont(ctx, 27);
    ctx.fillText(`${labels.score}: ${content.score}`, PADDING, y);
    y += 38;
  }

  if (content.lucky) {
    y += 6;
    ctx.fillStyle = COLORS.ink;
    measure = setFont(ctx, 25);
    for (const line of wrapText(luckyLine(content.lucky, labels), CONTENT_WIDTH, measure, 2)) {
      if (y > FOOTER_LINE_Y - 16) break;
      ctx.fillText(line, PADDING, y);
      y += 38;
    }
  }

  // フッター: 控えめな帰属表示（製品名とこのサイトのURL）
  ctx.fillStyle = COLORS.line;
  ctx.fillRect(PADDING, FOOTER_LINE_Y, CONTENT_WIDTH, 1);
  ctx.fillStyle = COLORS.accent;
  measure = setFont(ctx, 26, 700);
  ctx.fillText(labels.brand, PADDING, FOOTER_TEXT_Y);
  if (labels.site) {
    ctx.fillStyle = COLORS.muted;
    measure = setFont(ctx, 22);
    const siteWidth = measure(labels.site);
    ctx.fillText(labels.site, CARD_WIDTH - PADDING - siteWidth, FOOTER_TEXT_Y);
  }
  return canvas;
}

export function cardFileName(reading) {
  const engine = String(reading.engine_id ?? "").replace(/[^\w-]/g, "") || "reading";
  const date = String(reading.generated_at ?? "").slice(0, 10);
  return date ? `magi-${engine}-${date}.png` : `magi-${engine}.png`;
}

export function canShareFile(nav, file) {
  if (!nav || typeof nav.share !== "function" || typeof nav.canShare !== "function") return false;
  try {
    return nav.canShare({ files: [file] });
  } catch {
    return false;
  }
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  // 即座に revoke するとダウンロードが始まらないブラウザがあるため次のタスクで解放する。
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}

// カード画像を作って共有する。共有シートが使えなければダウンロードする。
// 戻り値: "shared" | "downloaded" | "cancelled"
export async function shareCardImage(reading, labels) {
  const canvas = renderCardImage(reading, labels);
  const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/png"));
  if (!blob) throw new Error("card image encoding failed");
  const file = new File([blob], cardFileName(reading), { type: "image/png" });
  if (canShareFile(navigator, file)) {
    try {
      await navigator.share({
        files: [file],
        title: `Magi — ${reading.engine_name ?? ""}`,
        text: String(reading.summary ?? ""),
      });
      return "shared";
    } catch (error) {
      if (error?.name === "AbortError") return "cancelled";
      // 共有に失敗した場合はダウンロードにフォールバックする。
    }
  }
  downloadBlob(blob, file.name);
  return "downloaded";
}
