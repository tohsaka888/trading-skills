# 工具调用手册

## 1. 环境检查
- 正式分析前，先检查 `uv` 是否可用。
- 必须确认以下本地脚本命令可执行：
  - `industry-name`
  - `fund-flow-rank`
  - `board-change`
  - `industry-spot`
  - `industry-hist`
  - `industry-hist-min`
- 固定使用当前 skill 自带脚本：`scripts/sector_data.py`
- 固定使用当前 skill 自带项目：`python/`
- 若 Eastmoney / Akshare 直连受限，需先配置以下环境变量后再运行脚本：
  - `TRADING_MCP_AKSHARE_PROXY_ENABLED`
  - `TRADING_MCP_AKSHARE_PROXY_AUTH_IP`
  - `TRADING_MCP_AKSHARE_PROXY_AUTH_TOKEN`
  - `TRADING_MCP_AKSHARE_PROXY_RETRY`
- 只有在 `TRADING_MCP_AKSHARE_PROXY_ENABLED=true` 且提供 `TRADING_MCP_AKSHARE_PROXY_AUTH_IP` 时，代理 patch 才会启用；`AUTH_TOKEN` 可选，`RETRY` 为重试次数。
- 优先通过 shell 导出环境变量，不依赖当前工作目录下 `.env` 是否被发现。
- 至少选择一个名称列表命令和一个行情命令做最小化试调用，确认不是依赖解析失败、脚本异常或上游服务异常。
- 任一关键命令异常时立即停止，并固定输出：
  - 错误类型
  - 失败命令名
  - 失败原因
  - 已停止本次盘中板块分析

## 2. 时段规则
- 盘中分析必须基于 `analysis_date` 和 `analysis_time` 的具体值，不允许使用相对时间表述。
- `09:35` 前：停止分析，明确写出“分时数据不足，不提供盘中结论”。
- `09:35-10:30`：只允许给出 `观察` 或 `轻仓回踩试错`；一律不输出“适合做T”。
- `10:30-14:30`：执行完整模型。
- `14:30-15:00`：允许给出 `持有`、`减仓`、`尾盘不追`，不建议新开激进做T。

## 3. 行业白名单
- 第一步固定执行：`uv run --project python python scripts/sector_data.py industry-name --limit 200`
- 后续命令返回的 `名称`、`板块名称` 等字段都必须先和白名单匹配。
- 无法匹配白名单的记录一律剔除，不进入候选池或 Top5。

## 4. 候选池工具

### `fund-flow-rank`
- 固定执行三组行业资金流：
  - `uv run --project python python scripts/sector_data.py fund-flow-rank --indicator 今日 --sector-type 行业资金流 --sort-by 主力净流入 --limit 20`
  - `uv run --project python python scripts/sector_data.py fund-flow-rank --indicator 5日 --sector-type 行业资金流 --sort-by 主力净流入 --limit 15`
  - `uv run --project python python scripts/sector_data.py fund-flow-rank --indicator 10日 --sector-type 行业资金流 --sort-by 主力净流入 --limit 10`
- 只保留行业白名单内的板块。

### `board-change`
- 固定执行 `uv run --project python python scripts/sector_data.py board-change --limit 100`。
- 按异动次数从高到低取前 `20` 个行业板块。
- 若脚本返回列名不是 `板块异动总次数`，则使用最能代表异动强度的次数列，并在报告中披露列名。

## 5. 预选分规则
- 今日资金强度：最高 `35`
- `5日` 持续性：最高 `15`
- `10日` 持续性：最高 `10`
- 异动活跃度：最高 `20`
- 实时强度：最高 `20`
- 实时强度必须在调用 `industry-spot --symbol <行业名>` 后补齐。
- 保留总分最高的前 `candidate_limit` 个板块；默认 `8`。

## 6. 深度分析工具

### `industry-spot`
- 对深度分析池逐一执行 `uv run --project python python scripts/sector_data.py industry-spot --symbol <行业名> --limit 30`。
- 重点提取：
  - 涨跌幅
  - 最新价
  - 成交额
  - 换手率
  - 振幅
  - 实时涨速或强弱字段
- 缺列时必须披露，不得补算。

### `industry-hist`
- 固定执行 `uv run --project python python scripts/sector_data.py industry-hist --symbol <行业名> --period 日k --adjust qfq --limit 40`。
- 固定提炼：
  - `5/10/20` 日均线关系
  - 近 `5` 日涨幅
  - 最新价相对 `20` 日均线偏离
  - 最近 `3` 根日K强弱
  - 量价位置和趋势完整性

### `industry-hist-min`
- 固定执行 `uv run --project python python scripts/sector_data.py industry-hist-min --symbol <行业名> --period 5 --limit 48`。
- 只使用 `5` 分钟分时，不允许降到 `1` 分钟。
- 固定提炼：
  - 开盘前 `30` 分钟强弱
  - 上午高点回吐幅度
  - 午后是否再强化
  - 当前价格在日内高低点区间的百分位
  - 分时回撤后是否有承接
  - 波动是否适合做T

## 7. 缺失和边界处理
1. 分时记录明显不足时：
- 继续分析，但降低 `分时结构质量` 权重
- 明确披露“分时样本不足，结论置信度下降”
2. 实时行情缺失成交额或换手率：
- 不补算
- 在对应板块条目直接写明“实时成交额数据缺失”或“实时换手率数据缺失”
3. 合格板块不足 `5` 个：
- 按实际数量输出
- 在市场状态摘要中写明“可执行板块数量不足”
4. 禁止调用：
- 个股资金流工具
- 个股技术指标工具
- 成分股工具
- 概念板块工具
