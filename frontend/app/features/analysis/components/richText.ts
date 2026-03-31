export interface TextSegment {
  text: string;
  highlight: boolean;
}

export function highlightSegments(text: string): TextSegment[] {
  // Match: decimals like 73.1, integers, percentages, score ranges like 84-79, ranks like No. 5 or #5
  const pattern = /\d+\.?\d*%|\d+\.?\d*\s*-\s*\d+\.?\d*|(?:No\.?|#)\s*\d+|\d+\.\d+|\b\d{2,}\b/g;
  const segments: TextSegment[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = pattern.exec(text)) !== null) {
    if (match.index > lastIndex) {
      segments.push({ text: text.slice(lastIndex, match.index), highlight: false });
    }
    segments.push({ text: match[0], highlight: true });
    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < text.length) {
    segments.push({ text: text.slice(lastIndex), highlight: false });
  }

  return segments.length > 0 ? segments : [{ text, highlight: false }];
}

export function splitIntoParagraphs(content: string) {
  const normalized = content.replace(/\r\n/g, "\n").trim();

  if (!normalized) return [];

  const explicitParagraphs = normalized
    .split(/\n\s*\n/)
    .map((paragraph) => paragraph.replace(/\s*\n\s*/g, " ").trim())
    .filter(Boolean);

  if (explicitParagraphs.length > 1) {
    return explicitParagraphs;
  }

  const sentences = normalized.match(/[^.!?]+[.!?]+|[^.!?]+$/g)?.map((sentence) => sentence.trim()) ?? [normalized];
  const paragraphs: string[] = [];

  for (let index = 0; index < sentences.length; index += 2) {
    const paragraph = sentences.slice(index, index + 2).join(" ").trim();
    if (paragraph) paragraphs.push(paragraph);
  }

  return paragraphs;
}
