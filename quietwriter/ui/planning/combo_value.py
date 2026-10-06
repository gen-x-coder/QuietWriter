from __future__ import annotations


def editable_combo_value(combo, *, default: str = "") -> str:
    """Return the canonical value for an editable combo without losing custom text.

    If the visible text still exactly matches the selected item, return that
    item's data. If the user typed the translated label of another known item,
    return that item's data. Otherwise preserve the custom visible text.
    """
    text = str(combo.currentText() or "").strip()
    index = int(combo.currentIndex())
    if index >= 0 and str(combo.itemText(index) or "").strip() == text:
        data = combo.itemData(index)
        if data is not None and str(data).strip():
            return str(data).strip()
    match = int(combo.findText(text)) if text else -1
    if match >= 0:
        data = combo.itemData(match)
        if data is not None and str(data).strip():
            return str(data).strip()
    return text or default
