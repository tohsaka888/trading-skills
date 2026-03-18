from __future__ import annotations

import argparse
import json

from trading_skills_data.errors import MarketDataError
from trading_skills_data.normalize import error_payload
from trading_skills_data.sectors import SectorDataClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Intraday sector data CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    industry_name = subparsers.add_parser("industry-name")
    industry_name.add_argument("--limit", type=int, default=30)
    industry_name.add_argument("--offset", type=int, default=0)

    fund_flow = subparsers.add_parser("fund-flow-rank")
    fund_flow.add_argument("--indicator", choices=["今日", "5日", "10日"], default="今日")
    fund_flow.add_argument("--sector-type", choices=["行业资金流", "概念资金流", "地域资金流"], default="行业资金流")
    fund_flow.add_argument("--sort-by", choices=["涨跌幅", "主力净流入"], default="主力净流入")
    fund_flow.add_argument("--limit", type=int, default=30)
    fund_flow.add_argument("--offset", type=int, default=0)

    board_change = subparsers.add_parser("board-change")
    board_change.add_argument("--limit", type=int, default=30)
    board_change.add_argument("--offset", type=int, default=0)

    industry_spot = subparsers.add_parser("industry-spot")
    industry_spot.add_argument("--symbol", required=True)
    industry_spot.add_argument("--limit", type=int, default=30)
    industry_spot.add_argument("--offset", type=int, default=0)

    industry_hist = subparsers.add_parser("industry-hist")
    industry_hist.add_argument("--symbol", required=True)
    industry_hist.add_argument("--period", choices=["日k", "周k", "月k"], default="日k")
    industry_hist.add_argument("--adjust", choices=["none", "qfq", "hfq"], default="none")
    industry_hist.add_argument("--limit", type=int, default=30)
    industry_hist.add_argument("--offset", type=int, default=0)
    industry_hist.add_argument("--start-date")
    industry_hist.add_argument("--end-date")

    industry_hist_min = subparsers.add_parser("industry-hist-min")
    industry_hist_min.add_argument("--symbol", required=True)
    industry_hist_min.add_argument("--period", choices=["1", "5", "15", "30", "60"], default="5")
    industry_hist_min.add_argument("--limit", type=int, default=30)
    industry_hist_min.add_argument("--offset", type=int, default=0)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    client = SectorDataClient()

    try:
        if args.command == "industry-name":
            payload = client.industry_name(limit=args.limit, offset=args.offset)
        elif args.command == "fund-flow-rank":
            payload = client.fund_flow_rank(
                indicator=args.indicator,
                sector_type=args.sector_type,
                sort_by=args.sort_by,
                limit=args.limit,
                offset=args.offset,
            )
        elif args.command == "board-change":
            payload = client.board_change(limit=args.limit, offset=args.offset)
        elif args.command == "industry-spot":
            payload = client.industry_spot(symbol=args.symbol, limit=args.limit, offset=args.offset)
        elif args.command == "industry-hist":
            payload = client.industry_hist(
                symbol=args.symbol,
                period=args.period,
                adjust=args.adjust,
                limit=args.limit,
                offset=args.offset,
                start_date=args.start_date,
                end_date=args.end_date,
            )
        elif args.command == "industry-hist-min":
            payload = client.industry_hist_min(
                symbol=args.symbol,
                period=args.period,
                limit=args.limit,
                offset=args.offset,
            )
        else:
            parser.error(f"Unsupported command: {args.command}")
            return 2
    except MarketDataError as exc:
        print(
            json.dumps(
                error_payload(
                    args.command,
                    {key: value for key, value in vars(args).items() if key != "command"},
                    "upstream_error",
                    str(exc),
                ),
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
