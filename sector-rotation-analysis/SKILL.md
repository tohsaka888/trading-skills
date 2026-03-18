---
name: sector-rotation-analysis
description: 面向A股全市场的板块轮动与潜力挖掘技能，按固定流程筛选行业板块候选池，结合行业资金流、板块历史行情、流动性质量与政策产业催化，分别输出短线轮动分与长线配置分，并生成详细报告与简短评分卡。当用户要求A股板块分析、板块轮动、潜力板块、长线配置方向、板块量化评分或板块投资建议时使用。
---

# 板块轮动分析

## 概述
按固定流程分析 A 股行业板块，输出短线机会、长线配置方向、潜力板块。以专业交易员口吻写作，强调收益风险比、资金持续性、流动性质量与中期趋势，不做情绪化追热点。

必须同时遵守硬约束：
1. 主评分宇宙固定为 A 股行业板块；概念板块只用于催化补充，不得混入主排名。
2. 必须分别给出短线分和长线分，不得合并成单一总分。
3. 结论必须以板块级数据为主，不做个股选股叙事，不输出个股推荐逻辑。

## 开始前必读
1. 阅读 `references/tool-playbook.md`，按固定顺序调用工具。
2. 阅读 `references/scoring-rules.md`，按统一打分和动作映射出结论。
3. 阅读 `references/output-format.md`，严格按模板输出。

## 可选输入
- `analysis_date`：分析日期；缺省时使用当前日期。
- `candidate_limit`：候选板块上限；缺省 `10`。

## 固定流程

### Phase 0: 环境检查与工具可用性验证
1. 在正式分析前，必须先检查 `uv` 可用，并使用当前 skill 自带的 `python/` 作为本地项目、`scripts/sector_data.py` 作为入口脚本执行命令。
2. 必须先对本地脚本做最小化试调用，确认关键能力可用：
- `uv run --project python python scripts/sector_data.py fund-flow-rank --indicator 今日 --sector-type 行业资金流 --sort-by 主力净流入 --limit 3`
- `uv run --project python python scripts/sector_data.py industry-hist --symbol <有效行业名> --period 日k --adjust qfq --limit 3`
3. 若 Eastmoney / Akshare 直连受限，必须先配置以下环境变量，再做最小化试调用：
- `TRADING_MCP_AKSHARE_PROXY_ENABLED`
- `TRADING_MCP_AKSHARE_PROXY_AUTH_IP`
- `TRADING_MCP_AKSHARE_PROXY_AUTH_TOKEN`
- `TRADING_MCP_AKSHARE_PROXY_RETRY`
4. 只有在 `TRADING_MCP_AKSHARE_PROXY_ENABLED=true` 且提供 `TRADING_MCP_AKSHARE_PROXY_AUTH_IP` 时，代理 patch 才会启用；`AUTH_TOKEN` 可选，`RETRY` 为重试次数。
5. 若 `uv` 不可用、脚本不可执行、依赖无法解析，或关键命令调用失败，必须立即停止，不得继续做板块分析。

### Phase 1: 构建候选池
1. 通过当前 skill 自带 uv 脚本调用 `fund-flow-rank` 三次，固定参数：
- `uv run --project python python scripts/sector_data.py fund-flow-rank --indicator 今日 --sector-type 行业资金流 --sort-by 主力净流入 --limit 30`
- `uv run --project python python scripts/sector_data.py fund-flow-rank --indicator 5日 --sector-type 行业资金流 --sort-by 主力净流入 --limit 30`
- `uv run --project python python scripts/sector_data.py fund-flow-rank --indicator 10日 --sector-type 行业资金流 --sort-by 主力净流入 --limit 30`
2. 候选入池规则固定：
- 任一窗口进入前 `20` 的行业板块入池。
- 用排名积分法聚合：第 1 名记 20 分，第 20 名记 1 分，未上榜记 0 分。
- 保留积分最高的前 `candidate_limit` 个板块，缺省为 `10`。

### Phase 2: 板块结构与流动性采集
对候选池中的每个候选行业板块，固定调用当前 skill 自带 uv 脚本：
1. `uv run --project python python scripts/sector_data.py industry-hist --symbol <行业名> --period 日k --adjust qfq --limit 10`
2. `uv run --project python python scripts/sector_data.py industry-hist --symbol <行业名> --period 周k --adjust qfq --limit 10`

从板块数据中提炼：
- 最新收盘相对 20 日均值的偏离
- 日线、周线趋势方向
- 最新成交量相对 5 日与 20 日均值的变化
- 最新成交额相对 5 日与 20 日均值的变化
- 量价是否同步放大
- 换手率水平与边际变化；若板块历史行情未返回换手率列，必须明确披露缺失

### Phase 3: 新闻与催化分析
1. 默认通过联网搜索检索近 `7` 天行业新闻与产业信息
2. 检索优先来源固定为：
- 监管机构或部委
- 行业协会、统计机构或产业链高可信度数据源
- 主流财经媒体
3. 每条事件按照以下格式进行梳理：
- 日期
- 事件标题
- 来源
- 类型：`政策监管 / 行业景气 / 产业链供需 / 黑天鹅`
- 方向：`利好 / 利空 / 中性`
- 影响期限：`短期 / 中期 / 长期`
- 可信度：`高 / 中 / 低`
- 一句话影响说明

### Phase 4: 双评分与动作建议
1. 按 `references/scoring-rules.md` 计算每个板块的短线分和长线分。
2. 固定输出四类结果：
- 短线关注 Top5
- 长线关注 Top5
- 潜力观察 Top3
3. 固定潜力板块定义：
- 长线分 `>= 70`
- 新闻面净判断为偏多
- 周线趋势未破坏且日线仍处于中期上行框架
- 流动性边际改善且不过热

## 高位风险提示
满足以下任意 `2` 条，即标记“短期过热”风险提示：
1. 板块近 `5` 个交易日涨幅 `> 15%`
2. 板块最新收盘偏离 `20` 日均价 `> 12%`
3. 最新成交量或成交额显著高于 `20` 日均值，且收盘承接不足或量价出现背离

若标记“短期过热”，短线动作最高只能给 `回踩参与`。

## 数据质量与回退
1. 数据缺失时，必须明确说明，不得补猜。
2. 环境检查未通过时：
- 直接报错并停止
- 不输出任何板块分析、评分卡或投资建议
- 必须向用户写明失败命令和失败原因
3. 所有时效信息必须写具体日期。

## 输出约束
1. 全文使用中文。
2. 以专业交易员口吻写作，不使用“可能还行”“看着不错”之类模糊表达。
3. 先讲结论，再给证据。
4. 报告必须同时包含详细报告和简短评分卡两层结果。
5. 严格按 `references/output-format.md` 的标题和字段输出。
6. 价值判断只能基于趋势、资金持续性、催化质量、拥挤度和收益风险比，不得虚构估值结论。
