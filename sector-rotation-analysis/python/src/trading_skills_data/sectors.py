from __future__ import annotations

from typing import Any, Literal

from requests.exceptions import ProxyError

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

import akshare_proxy_patch

_PATCH_INSTALLED = False


def install_akshare_proxy_patch() -> bool:
    global _PATCH_INSTALLED
    if _PATCH_INSTALLED:
        return True
    if akshare_proxy_patch is None or not hasattr(akshare_proxy_patch, "install_patch"):
        return False

    class AkshareProxyPatchSettings(BaseSettings):
        enabled: bool = Field(True)
        auth_ip: str | None = Field(None)
        auth_token: str = Field("")
        retry: int = Field(30, ge=1, le=200)

        model_config = SettingsConfigDict(
            env_prefix="TRADING_MCP_AKSHARE_PROXY_",
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",
        )

    settings = AkshareProxyPatchSettings()
    
    if not settings.enabled:
        return False

    if not settings.auth_ip:
        settings.auth_ip = "101.201.173.125"

    akshare_proxy_patch.install_patch(
        auth_ip=settings.auth_ip,
        auth_token=settings.auth_token,
        retry=settings.retry,
    )
    _PATCH_INSTALLED = True
    return True


install_akshare_proxy_patch()

import akshare as ak
import pandas as pd

from .errors import MarketDataError
from .normalize import dataframe_to_payload, sort_sector_rank

Indicator = Literal["今日", "5日", "10日"]
SectorType = Literal["行业资金流", "概念资金流", "地域资金流"]
SortBy = Literal["涨跌幅", "主力净流入"]
HistPeriod = Literal["日k", "周k", "月k"]
HistAdjust = Literal["none", "qfq", "hfq"]
MinPeriod = Literal["1", "5", "15", "30", "60"]


class SectorDataClient:
    def _ensure_frame(self, frame: pd.DataFrame | None) -> pd.DataFrame:
        if frame is None:
            return pd.DataFrame()
        return frame.reset_index(drop=True)

    def industry_name(self, *, limit: int, offset: int = 0) -> dict:
        params = {"limit": limit, "offset": offset}
        try:
            frame = self._ensure_frame(ak.stock_board_industry_name_em())
        except Exception as exc:
            raise MarketDataError(
                "Akshare EM industry names fetch failed; check upstream access and TRADING_MCP_AKSHARE_PROXY_* environment settings"
            ) from exc
        return dataframe_to_payload("industry-name", frame, params=params, limit=limit, offset=offset)

    def board_change(self, *, limit: int, offset: int = 0) -> dict:
        params = {"limit": limit, "offset": offset}
        try:
            frame = self._ensure_frame(ak.stock_board_change_em())
        except Exception as exc:
            raise MarketDataError("Akshare board change fetch failed; check upstream access and TRADING_MCP_AKSHARE_PROXY_* environment settings") from exc
        return dataframe_to_payload("board-change", frame, params=params, limit=limit, offset=offset)

    def industry_spot(self, *, symbol: str, limit: int, offset: int = 0) -> dict:
        params = {"symbol": symbol, "limit": limit, "offset": offset}
        try:
            frame = self._ensure_frame(ak.stock_board_industry_spot_em(symbol=symbol.strip()))
        except Exception as exc:
            raise MarketDataError(
                f"Akshare EM industry spot fetch failed for symbol={symbol}; check upstream access and TRADING_MCP_AKSHARE_PROXY_* environment settings"
            ) from exc
        return dataframe_to_payload("industry-spot", frame, params=params, limit=limit, offset=offset)

    def industry_hist(
        self,
        *,
        symbol: str,
        period: HistPeriod,
        adjust: HistAdjust,
        limit: int,
        offset: int = 0,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict:
        params = {
            "symbol": symbol,
            "period": period,
            "adjust": adjust,
            "limit": limit,
            "offset": offset,
            "start_date": start_date,
            "end_date": end_date,
        }
        try:
            frame = ak.stock_board_industry_hist_em(
                symbol=symbol.strip(),
                period=period,
                adjust="" if adjust == "none" else adjust,
                start_date=start_date,
                end_date=end_date,
            )
        except Exception as exc:
            raise MarketDataError(
                f"Akshare EM industry history fetch failed for symbol={symbol}, period={period}, adjust={adjust}; check upstream access and TRADING_MCP_AKSHARE_PROXY_* environment settings"
            ) from exc
        prepared = self._ensure_frame(frame)
        if not prepared.empty:
            prepared = prepared.iloc[::-1].reset_index(drop=True)
        return dataframe_to_payload("industry-hist", prepared, params=params, limit=limit, offset=offset)

    def industry_hist_min(
        self,
        *,
        symbol: str,
        period: MinPeriod,
        limit: int,
        offset: int = 0,
    ) -> dict:
        params = {"symbol": symbol, "period": period, "limit": limit, "offset": offset}
        try:
            frame = self._ensure_frame(
                ak.stock_board_industry_hist_min_em(symbol=symbol.strip(), period=period)
            )
        except Exception as exc:
            raise MarketDataError(
                f"Akshare EM industry intraday history fetch failed for symbol={symbol}, period={period}; check upstream access and TRADING_MCP_AKSHARE_PROXY_* environment settings"
            ) from exc
        if not frame.empty:
            frame = frame.iloc[::-1].reset_index(drop=True)
        return dataframe_to_payload("industry-hist-min", frame, params=params, limit=limit, offset=offset)

    def fund_flow_rank(
        self,
        *,
        indicator: Indicator,
        sector_type: SectorType,
        sort_by: SortBy,
        limit: int,
        offset: int = 0,
    ) -> dict:
        params = {
            "indicator": indicator,
            "sector_type": sector_type,
            "sort_by": sort_by,
            "limit": limit,
            "offset": offset,
        }
        try:
            frame = self._ensure_frame(
                ak.stock_sector_fund_flow_rank(indicator=indicator, sector_type=sector_type)
            )
        except Exception as exc:
            if isinstance(exc, ProxyError) or "ProxyError" in repr(exc):
                raise MarketDataError(
                    f"Akshare sector fund-flow ranking fetch failed for indicator={indicator}, sector_type={sector_type}; proxy connection failed, check TRADING_MCP_AKSHARE_PROXY_* settings and upstream reachability; raw_error={exc}"
                ) from exc
            raise MarketDataError(
                f"Akshare sector fund-flow ranking fetch failed for indicator={indicator}, sector_type={sector_type}; check upstream access and TRADING_MCP_AKSHARE_PROXY_* environment settings; raw_error={exc}"
            ) from exc
        sorted_frame = sort_sector_rank(frame, indicator, sort_by)
        return dataframe_to_payload(
            "fund-flow-rank",
            sorted_frame.reset_index(drop=True),
            params=params,
            limit=limit,
            offset=offset,
        )
