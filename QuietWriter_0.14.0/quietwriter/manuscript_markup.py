from __future__ import annotations

import re
from dataclasses import dataclass


_INLINE = {
    'bold': ('**', '**'),
    'italic': ('*', '*'),
    'underline': ('<u>', '</u>'),
    'strike': ('~~', '~~'),
    'code': ('`', '`'),
}

_BLOCK_PREFIX_RE = re.compile(r'^(?:##\s+|>\s+|[-*]\s+|\d+\.\s+)')


def is_scene_break_line(line: str) -> bool:
    """Return True for QuietWriter's protected scene-break sentinel."""
    return line.strip() == '***'


@dataclass(frozen=True)
class InlineSpan:
    """One paired inline-markup span in source coordinates.

    Marker coordinates deliberately stay separate from content coordinates.  This
    lets the editor hide the Markdown punctuation while composing multiple
    simultaneous styles (for example ``***bold italic***``) without the styles
    overwriting one another.
    """

    kind: str
    open_start: int
    open_end: int
    content_start: int
    content_end: int
    close_start: int
    close_end: int

    @property
    def marker_ranges(self) -> tuple[tuple[int, int], tuple[int, int]]:
        return ((self.open_start, self.open_end), (self.close_start, self.close_end))


def parse_inline_spans(text: str) -> list[InlineSpan]:
    """Parse QuietWriter's deliberately small inline-Markdown subset.

    This is not intended to be a complete CommonMark parser.  It only owns the
    syntax that QuietWriter itself can create: bold, italic, underline, strike
    and inline code.  Unpaired markers are left untouched and therefore remain
    visible to the writer instead of mysteriously disappearing.
    """

    spans: list[InlineSpan] = []
    opened: dict[str, tuple[int, int]] = {}
    i = 0
    n = len(text)

    def open_or_close(kind: str, start: int, end: int, *, close_start: int | None = None, close_end: int | None = None):
        if kind in opened:
            o_start, o_end = opened.pop(kind)
            c_start = start if close_start is None else close_start
            c_end = end if close_end is None else close_end
            if c_start >= o_end:
                spans.append(InlineSpan(kind, o_start, o_end, o_end, c_start, c_start, c_end))
        else:
            opened[kind] = (start, end)

    while i < n:
        # Inside inline code, every other formatting marker is literal.
        if 'code' in opened:
            if text.startswith('`', i):
                open_or_close('code', i, i + 1)
                i += 1
            else:
                i += 1
            continue

        if text.startswith('</u>', i):
            if 'underline' in opened:
                open_or_close('underline', i, i + 4)
            i += 4
            continue
        if text.startswith('<u>', i):
            if 'underline' not in opened:
                opened['underline'] = (i, i + 3)
            i += 3
            continue
        if text.startswith('`', i):
            open_or_close('code', i, i + 1)
            i += 1
            continue
        if text.startswith('~~', i):
            open_or_close('strike', i, i + 2)
            i += 2
            continue

        # Triple stars are QuietWriter's canonical representation of combined
        # bold+italic.  Treat the opening as ** + * and the closing as * + ** so
        # removing either style leaves valid Markdown for the other one.
        if text.startswith('***', i):
            bold_open = 'bold' in opened
            italic_open = 'italic' in opened
            if bold_open and italic_open:
                # Close italic with the first star and bold with the final two.
                o_start, o_end = opened.pop('italic')
                if i >= o_end:
                    spans.append(InlineSpan('italic', o_start, o_end, o_end, i, i, i + 1))
                o_start, o_end = opened.pop('bold')
                if i + 1 >= o_end:
                    spans.append(InlineSpan('bold', o_start, o_end, o_end, i + 1, i + 1, i + 3))
            elif not bold_open and not italic_open:
                opened['bold'] = (i, i + 2)
                opened['italic'] = (i + 2, i + 3)
            else:
                # Exactly one of bold/italic is already open. Treat the first
                # two stars as a normal bold token and leave the third for the
                # next parser step rather than hiding malformed source.
                open_or_close('bold', i, i + 2)
                i += 2
                continue
            i += 3
            continue
        if text.startswith('**', i):
            open_or_close('bold', i, i + 2)
            i += 2
            continue
        if text.startswith('*', i):
            open_or_close('italic', i, i + 1)
            i += 1
            continue
        i += 1

    spans.sort(key=lambda s: (s.open_start, -s.close_end, s.kind))
    return spans


def _merge_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    cleaned = sorted((a, b) for a, b in intervals if b > a)
    if not cleaned:
        return []
    merged = [cleaned[0]]
    for a, b in cleaned[1:]:
        pa, pb = merged[-1]
        if a <= pb:
            merged[-1] = (pa, max(pb, b))
        else:
            merged.append((a, b))
    return merged


def _subtract_interval(intervals: list[tuple[int, int]], cut: tuple[int, int]) -> list[tuple[int, int]]:
    ca, cb = cut
    out: list[tuple[int, int]] = []
    for a, b in intervals:
        if b <= ca or a >= cb:
            out.append((a, b))
            continue
        if a < ca:
            out.append((a, ca))
        if b > cb:
            out.append((cb, b))
    return _merge_intervals(out)


def _covered(intervals: list[tuple[int, int]], start: int, end: int) -> bool:
    if end <= start:
        return False
    cursor = start
    for a, b in _merge_intervals(intervals):
        if b <= cursor:
            continue
        if a > cursor:
            return False
        cursor = max(cursor, b)
        if cursor >= end:
            return True
    return False


def _strip_kind_markers(line: str, kind: str):
    all_spans = parse_inline_spans(line)
    spans = [span for span in all_spans if span.kind == kind]
    remove_ranges = _merge_intervals([
        rng for span in spans for rng in span.marker_ranges
    ])
    removed = [False] * len(line)
    for a, b in remove_ranges:
        for i in range(max(0, a), min(len(line), b)):
            removed[i] = True

    boundary_map = [0] * (len(line) + 1)
    out: list[str] = []
    for i, ch in enumerate(line):
        boundary_map[i] = len(out)
        if not removed[i]:
            out.append(ch)
    boundary_map[len(line)] = len(out)

    # Markers belonging to *other* styles can sit exactly on the inside edge of
    # a target span (canonical ***bold italic*** is the common case). They are
    # syntax, not visible content, so do not let the target style "own" those
    # marker characters when toggling one style off.
    other_markers = [
        (boundary_map[a], boundary_map[b])
        for span in all_spans if span.kind != kind
        for a, b in span.marker_ranges
    ]

    intervals = []
    for span in spans:
        a, b = boundary_map[span.content_start], boundary_map[span.content_end]
        changed = True
        while changed and b > a:
            changed = False
            for ma, mb in other_markers:
                if ma == a and mb <= b and mb > a:
                    a = mb; changed = True; break
            for ma, mb in other_markers:
                if mb == b and ma >= a and ma < b:
                    b = ma; changed = True; break
        if b > a:
            intervals.append((a, b))
    return ''.join(out), boundary_map, _merge_intervals(intervals)


def _serialize_kind(base: str, intervals: list[tuple[int, int]], kind: str):
    left, right = _INLINE[kind]
    intervals = _merge_intervals(intervals)
    starts = {a for a, _ in intervals}
    ends = {b for _, b in intervals}
    before = [0] * (len(base) + 1)
    after = [0] * (len(base) + 1)
    out: list[str] = []
    out_len = 0
    for i in range(len(base) + 1):
        before[i] = out_len
        if i in ends:
            out.append(right)
            out_len += len(right)
        if i in starts:
            out.append(left)
            out_len += len(left)
        after[i] = out_len
        if i < len(base):
            out.append(base[i])
            out_len += 1
    return ''.join(out), before, after


def _line_kind_state(line: str, start: int, end: int, kind: str) -> bool:
    base, boundary_map, intervals = _strip_kind_markers(line, kind)
    bs = boundary_map[max(0, min(start, len(line)))]
    be = boundary_map[max(0, min(end, len(line)))]
    if be <= bs:
        return False
    # Whitespace has no visible bold/italic distinction.  Trim it from the state
    # decision so selecting " word " behaves like selecting "word".
    while bs < be and base[bs].isspace():
        bs += 1
    while be > bs and base[be - 1].isspace():
        be -= 1
    return be > bs and _covered(intervals, bs, be)


def inline_style_state(text: str, start: int, end: int, kind: str) -> bool:
    """Return True only when the complete selected visible text has *kind*.

    A mixed selection deliberately returns False.  Clicking the toolbar action
    then normalises the whole selection to that style; clicking it again removes
    the style from the whole selection.  This mirrors common writing editors and
    is especially useful for selections containing a few already-italic words.
    """
    if kind not in _INLINE or start < 0 or end <= start or end > len(text):
        return False
    offset = 0
    saw_content = False
    for raw in text.splitlines(keepends=True):
        line = raw[:-1] if raw.endswith('\n') else raw
        line_start, line_end = offset, offset + len(line)
        a, b = max(start, line_start), min(end, line_end)
        if b > a and not is_scene_break_line(line):
            local_a, local_b = a - line_start, b - line_start
            if line[local_a:local_b].strip():
                saw_content = True
                if not _line_kind_state(line, local_a, local_b, kind):
                    return False
        offset += len(raw)
    return saw_content



def _trim_selection_markers(line: str, start: int, end: int) -> tuple[int, int]:
    """Move selection edges out of paired Markdown marker ranges.

    Qt selections are source-coordinate based while QuietWriter visually collapses
    markup punctuation.  After composing styles, canonical Markdown can reorder
    adjacent markers (``*`` + ``**`` becomes ``***``).  Normalising the returned
    range to visible content keeps subsequent toolbar actions semantic.
    """
    ranges = _merge_intervals([
        rng for span in parse_inline_spans(line) for rng in span.marker_ranges
    ])
    changed = True
    while changed:
        changed = False
        for a, b in ranges:
            if a <= start < b:
                start = b; changed = True; break
    changed = True
    while changed:
        changed = False
        for a, b in ranges:
            if a < end <= b:
                end = a; changed = True; break
    return min(start, end), max(start, end)

def _set_inline_line(line: str, start: int, end: int, kind: str, enabled: bool):
    all_spans = parse_inline_spans(line)
    base, boundary_map, intervals = _strip_kind_markers(line, kind)
    bs = boundary_map[max(0, min(start, len(line)))]
    be = boundary_map[max(0, min(end, len(line)))]
    if be <= bs:
        return line, start, end

    # Inline code is a protected literal region for every other style. Never
    # inject Markdown markers into the backticks or their content when a broad
    # selection crosses a code span. Map the complete code span to the current
    # base coordinates because target-kind markers may already have been stripped.
    selected_parts = [(bs, be)]
    if kind != 'code':
        protected = _merge_intervals([
            (boundary_map[span.open_start], boundary_map[span.close_end])
            for span in all_spans if span.kind == 'code'
        ])
        for cut in protected:
            selected_parts = _subtract_interval(selected_parts, cut)

    if enabled:
        intervals = _merge_intervals(intervals + selected_parts)
    else:
        for part in selected_parts:
            intervals = _subtract_interval(intervals, part)

    rendered, before, after = _serialize_kind(base, intervals, kind)
    # Start after markers inserted at the selection boundary; end before markers
    # at the far boundary. This keeps the user's visible text selected.
    new_start = after[bs]
    new_end = before[be]
    if new_end < new_start:
        new_end = new_start
    new_start, new_end = _trim_selection_markers(rendered, new_start, new_end)
    return rendered, new_start, new_end


def toggle_inline(text: str, start: int, end: int, kind: str) -> tuple[str, int, int]:
    """Toggle one inline style over a source selection, preserving other styles.

    The operation is semantic rather than delimiter-based.  If a selection is
    partly italic and partly plain, one click makes the *whole* selection italic;
    the next click makes the whole selection plain again. Existing bold,
    underline, strike or code markup is preserved.
    """
    if kind not in _INLINE or start < 0 or end <= start or end > len(text):
        return text, start, end

    enable = not inline_style_state(text, start, end, kind)
    out: list[str] = []
    offset = 0
    new_start: int | None = None
    new_end: int | None = None

    parts = text.splitlines(keepends=True)
    if not parts:
        return text, start, end

    for raw in parts:
        has_nl = raw.endswith('\n')
        line = raw[:-1] if has_nl else raw
        line_start, line_end = offset, offset + len(line)
        a, b = max(start, line_start), min(end, line_end)
        out_offset = sum(len(p) for p in out)
        if (b > a and not is_scene_break_line(line)
                and line[a-line_start:b-line_start].strip()):
            new_line, local_start, local_end = _set_inline_line(
                line, a - line_start, b - line_start, kind, enable
            )
            if new_start is None:
                new_start = out_offset + local_start
            new_end = out_offset + local_end
        else:
            new_line = line
        out.append(new_line + ('\n' if has_nl else ''))
        offset += len(raw)

    new_text = ''.join(out)
    if new_start is None or new_end is None:
        return text, start, end
    return new_text, new_start, new_end


def selected_line_range(text: str, start: int, end: int) -> tuple[int, int]:
    start = max(0, min(start, len(text)))
    end = max(start, min(end, len(text)))
    line_start = text.rfind('\n', 0, start) + 1
    nl = text.find('\n', end)
    line_end = len(text) if nl < 0 else nl
    return line_start, line_end


def _strip_block_prefix(line: str) -> str:
    return _BLOCK_PREFIX_RE.sub('', line, count=1)


def block_style_states(text: str, start: int, end: int) -> dict[str, bool]:
    ls, le = selected_line_range(text, start, end)
    lines = [line for line in text[ls:le].split('\n') if line.strip() and not is_scene_break_line(line)]
    if not lines:
        return {key: False for key in ('paragraph', 'heading', 'quote', 'bullet', 'numbered')}
    kinds = []
    for line in lines:
        if line.startswith('## '): kinds.append('heading')
        elif line.startswith('> '): kinds.append('quote')
        elif re.match(r'^[-*]\s+', line): kinds.append('bullet')
        elif re.match(r'^\d+\.\s+', line): kinds.append('numbered')
        else: kinds.append('paragraph')
    return {key: all(kind == key for kind in kinds) for key in ('paragraph', 'heading', 'quote', 'bullet', 'numbered')}


def selection_format_states(text: str, start: int, end: int) -> dict[str, bool]:
    states = block_style_states(text, start, end)
    for kind in _INLINE:
        states[kind] = inline_style_state(text, start, end, kind)
    return states


def apply_block_style(text: str, start: int, end: int, style: str) -> tuple[str, int, int]:
    """Apply/toggle a simple block style to all selected lines.

    ``heading`` deliberately uses ``##`` because a single ``#`` is reserved for
    QuietWriter chapter boundaries during Markdown import/export. Scene-break
    sentinels are structural and are therefore never transformed.
    """
    if not text:
        return text, start, end
    ls, le = selected_line_range(text, start, end)
    chunk = text[ls:le]
    lines = chunk.split('\n')

    transformable = [line for line in lines if line.strip() and not is_scene_break_line(line)]

    def transform(line: str, prefix: str, all_set: bool) -> str:
        if not line.strip() or is_scene_break_line(line):
            return line
        body = _strip_block_prefix(line)
        return body if all_set else prefix + body

    if style == 'paragraph':
        out = [line if is_scene_break_line(line) else (_strip_block_prefix(line) if line.strip() else line) for line in lines]
    elif style == 'heading':
        all_set = bool(transformable) and all(line.startswith('## ') for line in transformable)
        out = [transform(line, '## ', all_set) for line in lines]
    elif style == 'quote':
        all_set = bool(transformable) and all(line.startswith('> ') for line in transformable)
        out = [transform(line, '> ', all_set) for line in lines]
    elif style == 'bullet':
        all_set = bool(transformable) and all(line.startswith('- ') for line in transformable)
        out = [transform(line, '- ', all_set) for line in lines]
    elif style == 'numbered':
        all_set = bool(transformable) and all(re.match(r'^\d+\.\s+', line) for line in transformable)
        n = 1
        out = []
        for line in lines:
            if not line.strip() or is_scene_break_line(line):
                out.append(line)
                continue
            body = _strip_block_prefix(line)
            if all_set:
                out.append(body)
            else:
                out.append(f'{n}. {body}')
                n += 1
    else:
        return text, start, end

    replacement = '\n'.join(out)
    new_text = text[:ls] + replacement + text[le:]
    return new_text, ls, ls + len(replacement)


def smart_double_quote(text: str, position: int) -> str:
    """Return a typographic opening/closing double quote for the cursor context."""
    position = max(0, min(position, len(text)))
    before = text[:position]
    prev = before[-1] if before else ''
    if not prev or prev.isspace() or prev in '([{<—–-\n':
        return '“'
    return '”'


@dataclass(frozen=True)
class ManuscriptStyle:
    line_spacing_percent: int = 155
    paragraph_indent_px: int = 28
    paragraph_spacing_px: int = 8
    smart_quotes: bool = True

    @classmethod
    def from_settings(cls, settings):
        return cls.from_values(
            settings.value('manuscript_line_spacing', 155, int),
            settings.value('manuscript_indent', 28, int),
            settings.value('manuscript_paragraph_spacing', 8, int),
            settings.value('smart_quotes', True, bool),
        )

    @classmethod
    def from_values(cls, line_spacing=155, paragraph_indent=28, paragraph_spacing=8, smart_quotes=True):
        def _int(value, default, lo, hi):
            try: value = int(value)
            except (TypeError, ValueError): value = default
            return max(lo, min(hi, value))
        return cls(
            _int(line_spacing, 155, 120, 200),
            _int(paragraph_indent, 28, 0, 60),
            _int(paragraph_spacing, 8, 0, 24),
            bool(smart_quotes),
        )
