---
name: intraday-sector-analysis
description: 面向A股盘中实时行业板块交易的分时分析技能，基于 trading-mcp 的行业资金流、东方财富板块异动、行业实时行情、日线与5分钟分时结构，筛选当日最值得盯盘的五个行业板块，判断强弱持续性、是否适合做T、是否禁止追高，并输出专业交易员风格的极简交易卡。当用户要求盘中板块分析、分时板块分析、行业板块实时强弱、板块做T建议或当日板块战术建议时使用。
---

# 盘中板块分时交易分析

## 概述
按固定流程分析 A 股行业板块的盘中强弱、分时结构与执行机会。目标是优先捕捉当日最有盈利效率的行业板块，同时控制追高、回撤和流动性风险。

## 开始前必读
1. 阅读 `references/tool-playbook.md`，严格按工具顺序和时段规则执行。
2. 阅读 `references/scoring-rules.md`，严格按统一打分、风控门控和动作映射输出结论。
3. 阅读 `references/output-format.md`，严格按标题、字段和顺序输出。

## 可选输入
- `analysis_date`：分析日期；缺省时使用当前日期。
- `analysis_time`：分析时间；缺省时使用当前时间。
- `candidate_limit`：深度分析池上限；缺省 `8`。最终重点板块固定只输出 `5` 个。

## 固定流程

### Phase 0: 环境检查
1. 正式分析前，必须先确认 `trading-mcp` 已连接，且以下工具存在并可最小化试调用：
- `trading_industry_name_em`
- `trading_fund_flow_sector_rank_em`
- `trading_board_change_em`
- `trading_industry_spot_em`
- `trading_industry_hist_em`
- `trading_industry_hist_min_em`
2. 任一关键工具不存在、未注册、连接失败或服务异常，立即停止，不得继续分析。
3. 环境检查失败时只允许输出失败原因，不允许输出任何板块观点。

### Phase 1: 时段校验
1. 必须把 `analysis_date` 和 `analysis_time` 写成具体日期和时间。
2. 若时间早于 `09:35`，直接停止，明确写出“分时数据不足，不提供盘中结论”。
3. `09:35-10:30` 只允许输出 `观察` 或 `轻仓回踩试错`，不得给出正向“适合做T”结论。
4. `10:30-14:30` 执行完整模型。
5. `14:30-15:00` 可以判断持有、减仓、尾盘不追，但不建议新开激进做T。

### Phase 2: 预选池构建
1. 固定调用 `trading_fund_flow_sector_rank_em` 三次：
- `indicator='今日', sector_type='行业资金流', sort_by='主力净流入', limit=20`
- `indicator='5日', sector_type='行业资金流', sort_by='主力净流入', limit=15`
- `indicator='10日', sector_type='行业资金流', sort_by='主力净流入', limit=10`
2. 固定调用 `trading_board_change_em(limit=30)` 一次，并只保留能匹配行业白名单的记录。
3. 候选池固定为以下并集：
- 今日资金流前 `20`
- `5日` 资金流前 `15`
- `10日` 资金流前 `10`
- 板块异动活跃前 `20`
4. 预选分固定构成：
- 今日资金强度 `35`
- `5日` 持续性 `15`
- `10日` 持续性 `10`
- 异动活跃度 `20`
- 实时强度预留 `20`
5. 保留预选分最高的前 `candidate_limit` 个板块，缺省 `8` 个进入深度分析。

### Phase 3: 深度分析
对深度分析池中的每个行业板块，固定调用：
1. `trading_industry_spot_em(symbol, limit=30)`
2. `trading_industry_hist_em(symbol, period='日k', adjust='qfq', limit=10)`
3. `trading_industry_hist_min_em(symbol, period='5', limit=30)`

必须从结果中提炼：
- 上午高点是否明显回吐
- 午后是否再强化或再创新高
- 当前价格处于日内高低区间的百分位
- 分时回撤后是否有承接
- 是否存在适合做T的震荡与回落买点结构

### Phase 4: 评分、动作与排序
1. 按 `references/scoring-rules.md` 计算每个板块的：
- `盘中关注分`
- `做T适配分`
- 是否禁止追高
- 建议动作
2. 最终只输出 `盘中关注分` 最高的 `5` 个行业板块。
3. 每个板块都必须明确回答：
- 是否适合做T
- 当前更适合顺势、回踩、观察还是回避
- 触发条件
- 失效条件
- 核心风险

## 数据质量与回退
1. 字段缺失时必须明确披露，不得补猜。
2. `trading_industry_hist_min_em` 数据不足时，必须降低分时结构权重并写明置信度下降。
3. `trading_industry_spot_em` 缺失成交额或换手率时，不得补算，只能降权并披露。
4. 若合格板块不足 `5` 个，按实际数量输出，并说明市场机会不足。

## 输出约束
1. 全文使用中文。
2. 以专业交易员口吻写作，强调收益风险比、执行窗口、追高风险和失效条件。
3. 先讲结论，再给证据。
4. 严格按 `references/output-format.md` 格式输出。
5. 所有时效信息必须写具体日期和时间。
