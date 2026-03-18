# 工具调用手册

## 1. 环境检查
- 正式分析前，先检查 `uv` 是否可用。
- 必须先确认以下关键命令可调用：
  - `fund-flow-rank`
  - `industry-hist`
- 固定使用当前 skill 自带脚本：`scripts/sector_data.py`
- 固定使用当前 skill 自带项目：`python/`
- 若 Eastmoney / Akshare 直连受限，需先配置以下环境变量后再运行脚本：
  - `TRADING_MCP_AKSHARE_PROXY_ENABLED`
  - `TRADING_MCP_AKSHARE_PROXY_AUTH_IP`
  - `TRADING_MCP_AKSHARE_PROXY_AUTH_TOKEN`
  - `TRADING_MCP_AKSHARE_PROXY_RETRY`
- 只有在 `TRADING_MCP_AKSHARE_PROXY_ENABLED=true` 且提供 `TRADING_MCP_AKSHARE_PROXY_AUTH_IP` 时，代理 patch 才会启用；`AUTH_TOKEN` 可选，`RETRY` 为重试次数。
- 优先通过 shell 导出环境变量，不依赖当前工作目录下 `.env` 是否被发现。
- 至少选择一个关键命令做最小化试调用，确认不是依赖解析失败、脚本异常或上游服务异常。
- 若关键命令不存在，或试调用返回 uv 运行失败、脚本参数错误、上游数据异常，立即停止分析并直接报错给用户。
- 报错时固定包含：
  - 错误类型
  - 失败命令名
  - 失败原因
  - 已停止本次分析

## 2. 主评分宇宙
- 主评分宇宙固定为 `行业资金流`。

## 3. 候选池工具

### `fund-flow-rank`
- 固定执行三组行业资金流：`今日`、`5日`、`10日`
- 固定参数：`sector_type='行业资金流'`
- 对应命令：`uv run --project python python scripts/sector_data.py fund-flow-rank --indicator <今日|5日|10日> --sector-type 行业资金流 --sort-by 主力净流入 --limit 30`
- `主力净流入` 由脚本按 Akshare 文档语义兼容解析上游字段，优先匹配 `主力净流入-净额` 及其时间窗口变体；若试调用已成功返回数据，但不存在任何可解析的主力净流入语义字段，则必须停止本次量化分析并报告实际返回列名。
- 若抓取阶段直接报代理连接失败或上游连接失败，应优先排查 `TRADING_MCP_AKSHARE_PROXY_*` 配置与 Eastmoney 可达性，而不是直接判定为字段漂移。
- 候选入池条件：任一行业窗口进入前 `20`

### 候选池积分法
- 第 `1-20` 名分别记 `20-1` 分
- 三个窗口积分求和
- 保留前 `candidate_limit` 个板块；默认 `10`

## 4. 板块结构工具

### `industry-hist`
- 对每个候选板块固定取：
  - `period='日k'`
  - `period='周k'`
- `adjust='qfq'`
- 对应命令：`uv run --project python python scripts/sector_data.py industry-hist --symbol <行业名> --period <日k|周k> --adjust qfq --limit 10`
- 每个周期固定只使用最近 `10` 条数据；若无显式 `limit` 参数，则截取返回结果的最近 `10` 条
- 固定提炼：
  - 近 5 日涨跌幅
  - 日线与周线趋势方向
  - 板块相对 20 日均线偏离
  - 最新成交量相对 5 日与 20 日均值变化
  - 最新成交额相对 5 日与 20 日均值变化
  - 量价是否同步放大
  - 换手率水平与边际变化；若无换手率列则披露缺失
- 禁止补充调用任何成分股清单、个股行情、个股资金流或涨跌家数数据

## 5. 新闻工具

### 联网搜索
- 默认通过联网搜索检索
- 默认窗口近 `7` 天，必要时扩展到 `30` 天
- 组合检索词：
  - 板块名
  - 上游关键词
  - 下游关键词
  - 政策关键词
  - 景气、订单、涨价、招标、监管等产业词

### 来源优先级
1. 政策与监管
2. 行业协会、统计机构或产业链高可信度数据源
3. 主流财经媒体

## 6. 失败回退
1. 环境检查未通过：直接报错并停止，不进入板块分析
2. 单个板块工具失败：用剩余数据继续，但降低置信度
3. 新闻过少：扩窗至 30 天；仍不足则降低新闻权重并披露
4. 若板块历史行情缺少 `换手率` 列：明确写出“板块换手率数据缺失”，不得用个股或成分股数据补位
