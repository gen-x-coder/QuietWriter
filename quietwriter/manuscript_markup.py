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
                # At a boundary between italic and bold, three adjacent stars
                # are the canonical close-one/open-the-other transition.
                # Resolve them according to the style that is already open.
                if italic_open:
                    open_or_close('italic', i, i + 1)
                    opened['bold'] = (i + 1, i + 3)
                else:
                    open_or_close('bold', i, i + 2)
                    opened['italic'] = (i + 2, i + 3)
                i += 3
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


def source_selection_with_enclosing_markup(text: str, start: int, end: int) -> tuple[int, int]:
    """Expand visible selection edges to include paired inline Markdown markers.

    QuietWriter visually collapses its own inline punctuation. Qt cursor positions
    can therefore select exactly the visible content of ``**bold**`` while the
    persistent source range would otherwise omit the boundary markers. Internal
    markers already fall inside the range; only paired markers touching either
    selection edge need expansion.
    """
    if start < 0 or end <= start or end > len(text):
        return start, end
    a, b = start, end
    changed = True
    spans = parse_inline_spans(text)
    while changed:
        changed = False
        for span in spans:
            if a == span.content_start and b >= span.content_end and span.open_start < a:
                a = span.open_start
                changed = True
            if b == span.content_end and a <= span.content_start and span.close_end > b:
                b = span.close_end
                changed = True
    return a, b


def source_selection_as_markdown(text: str, start: int, end: int) -> tuple[str, int, int]:
    """Return a self-contained Markdown fragment for a visible source selection.

    Full inline spans keep their original markers. When a selection starts or
    ends *inside* a formatted span, matching boundary markers are synthesized
    around the selected text instead of leaving a dangling marker behind. The
    returned coordinates describe the source range used for context anchors.
    """
    if start < 0 or end <= start or end > len(text):
        return '', start, end

    source_start, source_end = source_selection_with_enclosing_markup(text, start, end)
    selected = text[source_start:source_end]
    spans = parse_inline_spans(text)

    opening = []
    closing = []
    for span in spans:
        # No selected visible content from this span.
        if end <= span.content_start or start >= span.content_end:
            continue
        opener, closer = _INLINE[span.kind]
        opener_in_selection = source_start <= span.open_start and span.open_end <= source_end
        closer_in_selection = source_start <= span.close_start and span.close_end <= source_end
        if not opener_in_selection:
            opening.append((span.open_start, opener))
        if not closer_in_selection:
            closing.append((span.close_start, closer))

    # Preserve original nesting order. For *** this yields ** + * at the start
    # and * + ** at the end, i.e. valid combined bold/italic Markdown.
    opening_text = ''.join(marker for _, marker in sorted(opening, key=lambda item: item[0]))
    closing_text = ''.join(marker for _, marker in sorted(closing, key=lambda item: item[0]))
    return opening_text + selected + closing_text, source_start, source_end


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



class UnsafeMarkdownInsertionError(ValueError):
    """Raised when a Darling cannot be inserted without changing visible formatting."""


def _source_style_map(text: str):
    """Return marker flags and active inline styles in linear time.

    The previous implementation scanned every span for every source character,
    which became quadratic in long formatted chapters.  There are only five
    QuietWriter inline kinds, so difference arrays keep this O(text + spans).
    """
    spans = parse_inline_spans(text)
    n = len(text)
    marker = bytearray(n)
    diffs = {kind: [0] * (n + 1) for kind in _INLINE}
    for span in spans:
        for a, b in span.marker_ranges:
            a = max(0, min(a, n)); b = max(a, min(b, n))
            marker[a:b] = b'\x01' * (b - a)
        if span.kind in diffs:
            a = max(0, min(span.content_start, n)); b = max(a, min(span.content_end, n))
            diffs[span.kind][a] += 1
            diffs[span.kind][b] -= 1
    active = {kind: 0 for kind in _INLINE}
    styles = [frozenset()] * n
    for i in range(n):
        for kind in _INLINE:
            active[kind] += diffs[kind][i]
        styles[i] = frozenset(kind for kind, count in active.items() if count > 0)
    return marker, styles


def _visible_projection(text: str, position: int | None = None):
    marker, styles = _source_style_map(text)
    limit = None if position is None else min(max(0, position), len(text))
    offset = 0
    visible = []
    for i, ch in enumerate(text):
        if marker[i]:
            continue
        if limit is not None and i < limit:
            offset += 1
        visible.append((ch, styles[i]))
    return visible, offset


def _visible_text_with_styles(text: str):
    return _visible_projection(text)[0]


def _visible_offset_for_source_position(text: str, position: int) -> int:
    return _visible_projection(text, position)[1]


def _minimal_replacement(original: str, changed: str) -> tuple[int, int, str]:
    """Return the smallest single source splice turning *original* into *changed*."""
    prefix = 0
    limit = min(len(original), len(changed))
    while prefix < limit and original[prefix] == changed[prefix]:
        prefix += 1
    suffix = 0
    original_left = len(original) - prefix
    changed_left = len(changed) - prefix
    while suffix < original_left and suffix < changed_left and original[-1 - suffix] == changed[-1 - suffix]:
        suffix += 1
    original_end = len(original) - suffix
    changed_end = len(changed) - suffix
    return prefix, original_end, changed[prefix:changed_end]


def prepare_markdown_removal(text: str, start: int, end: int) -> tuple[int, int, str]:
    """Return a safe single source splice for *Cut to Darlings*.

    The first candidates remove a contiguous source range.  A third candidate
    removes only the selected *visible* characters while retaining Markdown
    marker characters.  That makes common half-bold/half-italic selections
    practical without weakening the fail-closed validation: every candidate is
    reparsed and must preserve the exact visible text and per-character styles
    of everything that remains.
    """
    if start < 0 or end <= start or end > len(text):
        raise UnsafeMarkdownInsertionError('Ongeldige selectie.')
    base_visible = _visible_text_with_styles(text)
    start_offset = _visible_offset_for_source_position(text, start)
    end_offset = _visible_offset_for_source_position(text, end)
    expected = base_visible[:start_offset] + base_visible[end_offset:]

    _fragment, source_start, source_end = source_selection_as_markdown(text, start, end)
    candidates: list[tuple[int, int, str]] = [(source_start, source_end, '')]
    if (source_start, source_end) != (start, end):
        candidates.append((start, end, ''))

    # Qt selections can begin/end inside an inline span.  For that case keep
    # marker characters that fall inside the selected source range and remove
    # only visible characters.  This can leave a small replacement rather than
    # a pure deletion, hence the splice carries replacement text explicitly.
    marker, _styles = _source_style_map(text)
    emptied_marker_indices = set()
    for span in parse_inline_spans(text):
        visible_content = [
            i for i in range(span.content_start, span.content_end)
            if not marker[i]
        ]
        if visible_content and all(start <= i < end for i in visible_content):
            for a, b in span.marker_ranges:
                emptied_marker_indices.update(range(a, b))

    visible_only = ''.join(
        ch for i, ch in enumerate(text)
        if i not in emptied_marker_indices
        and not (start <= i < end and not marker[i])
    )
    if visible_only != text:
        candidates.append(_minimal_replacement(text, visible_only))

    seen = set()
    for a, b, replacement in candidates:
        key = (a, b, replacement)
        if key in seen:
            continue
        seen.add(key)
        if not (0 <= a <= b <= len(text)) or (a == b and not replacement):
            continue
        result = text[:a] + replacement + text[b:]
        empty_tokens = ('****', '~~~~', '``', '<u></u>')
        if any(result.count(token) > text.count(token) for token in empty_tokens):
            continue
        if _visible_text_with_styles(result) == expected:
            return a, b, replacement
    raise UnsafeMarkdownInsertionError('Knippen zou bestaande Markdown-opmaak wijzigen.')


def _validated_insertion(text: str, original_position: int, position: int, insertion: str, fragment: str):
    base_visible, offset = _visible_projection(text, original_position)
    fragment_visible = _visible_text_with_styles(fragment)
    expected = base_visible[:offset] + fragment_visible + base_visible[offset:]
    result = text[:position] + insertion + text[position:]
    if _visible_text_with_styles(result) != expected:
        raise UnsafeMarkdownInsertionError('Invoegen zou bestaande Markdown-opmaak wijzigen.')
    return position, insertion


def prepare_markdown_insertion(text: str, position: int, fragment: str) -> tuple[int, str]:
    """Return a source-safe insertion for a Darling or refuse the operation.

    QTextCursor can land inside hidden Markdown marker runs.  We first move such
    positions to a visually equivalent boundary.  Inside formatted content we
    temporarily close the active styles, insert the fragment with its own
    formatting, and reopen the surrounding styles.  Matching markers at the two
    seams are collapsed where possible.  The complete result is then parsed and
    compared with the expected visible text *and style per character*.  If that
    proof fails, insertion is refused rather than risking manuscript damage.
    """
    original_position = max(0, min(position, len(text)))
    position = original_position
    spans = parse_inline_spans(text)

    changed = True
    while changed:
        changed = False
        for span in spans:
            if span.open_start < position < span.open_end:
                position = span.open_start
                changed = True
                break
            if span.close_start < position < span.close_end:
                position = span.close_end
                changed = True
                break
            if position == span.content_start:
                position = span.open_start
                changed = True
                break
            if position == span.content_end:
                position = span.close_end
                changed = True
                break

    # At an exact boundary, a fragment wholly wrapped in the same style can
    # safely inherit that adjacent span. This avoids creating ambiguous touching
    # marker runs such as ``**a****b**`` while preserving the exact visible style.
    fragment_spans = parse_inline_spans(fragment)
    for span in spans:
        if position not in (span.open_start, span.close_end):
            continue
        full = next((
            f for f in fragment_spans
            if f.kind == span.kind and f.open_start == 0 and f.close_end == len(fragment)
        ), None)
        if full is None:
            continue
        remove = set()
        for a, b in full.marker_ranges:
            remove.update(range(a, b))
        stripped = ''.join(ch for i, ch in enumerate(fragment) if i not in remove)
        merged_position = span.content_start if position == span.open_start else span.content_end
        try:
            return _validated_insertion(text, original_position, merged_position, stripped, fragment)
        except UnsafeMarkdownInsertionError:
            pass

    active = [span for span in spans if span.content_start < position < span.content_end]
    if not active:
        return _validated_insertion(text, original_position, position, fragment, fragment)

    active.sort(key=lambda s: (s.open_start, -s.close_end, s.kind))
    fragment_spans = parse_inline_spans(fragment)
    inherited_kinds = {
        span.kind for span in fragment_spans
        if span.open_start == 0 and span.close_end == len(fragment)
        and any(active_span.kind == span.kind for active_span in active)
    }
    body = fragment
    if inherited_kinds:
        remove = set()
        for span in fragment_spans:
            if span.kind in inherited_kinds and span.open_start == 0 and span.close_end == len(fragment):
                for a, b in span.marker_ranges:
                    remove.update(range(a, b))
        body = ''.join(ch for i, ch in enumerate(fragment) if i not in remove)

    split_spans = [span for span in active if span.kind not in inherited_kinds]
    if not split_spans:
        return _validated_insertion(text, original_position, position, body, fragment)

    closer_tokens = [(span.kind, text[span.close_start:span.close_end]) for span in reversed(split_spans)]
    opener_tokens = [(span.kind, text[span.open_start:span.open_end]) for span in split_spans]

    # Left seam: keep an already-active style open when the fragment begins
    # with the same style.  Example: **v|et** + **x** -> **vx**...
    while closer_tokens:
        kind, _close = closer_tokens[-1]
        open_marker = _INLINE[kind][0]
        parsed_body = parse_inline_spans(body)
        matching = any(
            span.kind == kind and span.open_start == 0 and span.open_end == len(open_marker)
            for span in parsed_body
        )
        if not matching:
            break
        closer_tokens.pop()
        body = body[len(open_marker):]

    # Right seam: likewise let a matching style at the end of the fragment
    # flow directly into the reopened source style.
    while opener_tokens:
        kind, _open = opener_tokens[0]
        close_marker = _INLINE[kind][1]
        parsed_body = parse_inline_spans(body)
        matching = any(
            span.kind == kind and span.close_end == len(body)
            and span.close_start == len(body) - len(close_marker)
            for span in parsed_body
        )
        if not matching:
            break
        opener_tokens.pop(0)
        body = body[:-len(close_marker)] if close_marker else body

    closers = ''.join(token for _kind, token in closer_tokens)
    openers = ''.join(token for _kind, token in opener_tokens)
    insertion = closers + body + openers
    return _validated_insertion(text, original_position, position, insertion, fragment)


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
