from __future__ import annotations

from collections.abc import Iterable
import re
from typing import Any

import pandas as pd

from .errors import MarketDataError

SECTOR_RANK_SORT_CANDIDATES: dict[tuple[str, str], tuple[str, ...]] = {
    ("今日", "主力净流入"): (
        "主力净流入-净额",
        "主力净流入",
        "主力净流入净额",
        "今日主力净流入-净额",
        "今日主力净流入",
        "今日主力净流入净额",
    ),
    ("5日", "主力净流入"): (
        "5日主力净流入-净额",
        "5日主力净流入",
        "5日主力净流入净额",
        "主力净流入-净额",
        "主力净流入",
        "主力净流入净额",
    ),
    ("10日", "主力净流入"): (
        "10日主力净流入-净额",
        "10日主力净流入",
        "10日主力净流入净额",
        "主力净流入-净额",
        "主力净流入",
        "主力净流入净额",
    ),
    ("今日", "涨跌幅"): ("今日涨跌幅", "涨跌幅"),
    ("5日", "涨跌幅"): ("5日涨跌幅", "涨跌幅"),
    ("10日", "涨跌幅"): ("10日涨跌幅", "涨跌幅"),
}


def _json_safe(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    return value


def dataframe_to_payload(
    tool: str,
    frame: pd.DataFrame | None,
    *,
    params: dict[str, Any],
    limit: int,
    offset: int = 0,
    latest: bool = True,
) -> dict[str, Any]:
    normalized = frame.copy() if frame is not None else pd.DataFrame()
    if normalized.empty:
        window = normalized
    else:
        start = max(offset, 0)
        if latest:
            window = normalized.iloc[start : start + limit]
        else:
            window = normalized.iloc[start : start + limit]
    columns = [str(column) for column in window.columns.tolist()]
    items = [
        {str(key): _json_safe(value) for key, value in record.items()}
        for record in window.to_dict(orient="records")
    ]
    total = 0 if frame is None else int(len(frame.index))
    count = int(len(items))
    next_offset = offset + count if offset + count < total else None
    return {
        "ok": True,
        "tool": tool,
        "params": params,
        "columns": columns,
        "items": items,
        "meta": {
            "count": count,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": next_offset is not None,
            "next_offset": next_offset,
        },
    }


def _normalize_column_name(column: str) -> str:
    return re.sub(r"[\s\-_/（）()]+", "", str(column)).lower()


def _resolve_sector_rank_column(columns: Iterable[str], indicator: str, sort_by: str) -> str | None:
    available = [str(column) for column in columns]
    candidates = SECTOR_RANK_SORT_CANDIDATES.get((indicator, sort_by), ())

    exact_match = choose_first_column(available, candidates)
    if exact_match:
        return exact_match

    normalized_map = {_normalize_column_name(column): column for column in available}
    for candidate in candidates:
        normalized_candidate = _normalize_column_name(candidate)
        if normalized_candidate in normalized_map:
            return normalized_map[normalized_candidate]

    if sort_by != "主力净流入":
        return None

    indicator_tokens = {
        "今日": tuple(),
        "5日": ("5日",),
        "10日": ("10日",),
    }.get(indicator, tuple())

    best_column: str | None = None
    best_score = -1
    for column in available:
        normalized = _normalize_column_name(column)
        if "主力" not in normalized or "净流入" not in normalized:
            continue
        if any(token not in normalized for token in indicator_tokens):
            continue
        score = 0
        if "净额" in normalized:
            score += 4
        if "占比" in normalized or "比例" in normalized or "净占比" in normalized:
            score -= 5
        if indicator != "今日" and any(token in normalized for token in ("今日", "当日")):
            score -= 3
        if indicator == "今日" and any(token in normalized for token in ("5日", "10日")):
            score -= 3
        score += len(normalized)
        if score > best_score:
            best_score = score
            best_column = column
    return best_column


def sort_sector_rank(frame: pd.DataFrame, indicator: str, sort_by: str) -> pd.DataFrame:
    candidates = SECTOR_RANK_SORT_CANDIDATES.get((indicator, sort_by), ())
    column = _resolve_sector_rank_column(frame.columns, indicator, sort_by)
    if column is None:
        if not candidates:
            return frame.reset_index(drop=True)
        raise MarketDataError(
            f"Sector rank sorting failed for indicator={indicator}, sort_by={sort_by}; expected aliases={list(candidates)}; actual columns={list(map(str, frame.columns))}"
        )

    sorted_frame = frame.copy()
    sorted_frame[column] = pd.to_numeric(sorted_frame[column], errors="coerce")
    if sorted_frame[column].notna().sum() == 0:
        raise MarketDataError(
            f"Sector rank sorting failed for indicator={indicator}, sort_by={sort_by}; resolved column={column} but all values are non-numeric; actual columns={list(map(str, frame.columns))}"
        )
    return sorted_frame.sort_values(by=column, ascending=False, na_position="last")


def choose_first_column(columns: Iterable[str], candidates: Iterable[str]) -> str | None:
    available = {str(column) for column in columns}
    for candidate in candidates:
        if candidate in available:
            return candidate
    return None


def error_payload(tool: str, params: dict[str, Any], error_type: str, error: str) -> dict[str, Any]:
    return {
        "ok": False,
        "tool": tool,
        "params": params,
        "error_type": error_type,
        "error": error,
    }
