---
name: sector-rotation-analysis
description: 面向A股全市场的板块轮动分析技能，按固定流程筛选行业板块候选池，结合行业资金流、板块历史行情、板块成份股与龙头股技术面、新闻催化和追高约束，分别输出短线轮动分与长线配置分，并生成详细报告与简短评分卡。当用户要求A股板块分析、板块轮动、短线热点板块、长线配置方向、板块量化评分或板块投资建议时使用。
---

# 板块轮动分析

## 概述
按固定流程分析 A 股行业板块，输出短线机会、长线配置方向、潜力板块和回避板块。使用投资分析师口吻写作，优先关注收益风险比，禁止因为短期热度而机械追高。

必须同时遵守四条硬约束：
1. 主评分宇宙固定为 A 股行业板块；概念板块只用于催化补充，不得混入主排名。
2. 必须分别给出短线分和长线分，不得合并成单一总分。
3. 必须检查追高风险；满足规则时，明确标记“禁止追高”并下调短线动作上限。
4. 必须使用外部注入 session；本技能内禁止创建新 session。

## 开始前必读
1. 阅读 `references/tool-playbook.md`，按固定顺序调用工具。
2. 阅读 `references/scoring-rules.md`，按统一打分和动作映射出结论。
3. 阅读 `references/output-format.md`，严格按模板输出。
4. 需要扩展新闻检索词时，阅读 `references/news-keywords.md`。

## 必填输入
调用方必须提供以下字段；缺任一字段都必须报错并停止：
- `session_dir`：绝对路径，例如 `/abs/path/to/sessions/2026-03-13_板块轮动分析`
- `session_dir_rel`：相对工作区路径，例如 `sessions/2026-03-13_板块轮动分析`

## 可选输入
- `analysis_date`：分析日期；缺省时使用当前日期。
- `candidate_limit`：候选板块上限；缺省 `12`。

## Session 约束
1. 校验 `session_dir` 和 `session_dir_rel` 同时存在。
2. 校验两者末级目录一致；不一致则报错停止。
3. 全流程只允许写入调用方提供的 session。
4. 在 `${session_dir_rel}/板块候选池.md` 先记录：
- 分析日期
- 主评分宇宙定义
- 可用工具列表
- 不可用工具及影响范围

## 固定流程

### Phase 0: 工具可用性与板块宇宙检查
1. 确认是否可调用以下本地工具：
- `trading_fund_flow_sector_rank_em`
- `trading_fund_flow_sector_summary_em`
- `trading_industry_hist_em`
- `trading_industry_hist_min_em`
- `trading_industry_cons_em`
- `trading_kline`
- `trading_ma`
- `trading_macd`
- `trading_rsi`
- `trading_volume`
- `trading_fund_flow_individual_em`
2. 确认 `stock_news_em` 是否可用：
- 可用时，优先用它做板块新闻和关键词检索。
- 不可用时，必须改用联网搜索监管机构、交易所公告和主流财经媒体。
3. 明确写出：主评分宇宙使用“行业资金流”；“概念资金流”仅做催化辅助。

### Phase 1: 构建候选池
1. 调用 `trading_fund_flow_sector_rank_em` 三次，固定参数：
- `indicator='今日', sector_type='行业资金流'`
- `indicator='5日', sector_type='行业资金流'`
- `indicator='10日', sector_type='行业资金流'`
2. 候选入池规则固定：
- 任一窗口进入前 `20` 的行业板块入池。
- 用排名积分法聚合：第 1 名记 20 分，第 20 名记 1 分，未上榜记 0 分。
- 保留积分最高的前 `candidate_limit` 个板块，缺省为 `12`。
3. 辅助拉取概念资金流：
- 对 `今日/5日/10日 + 概念资金流` 各拉取一次。
- 只用于识别跨行业催化主题，不参与主候选池打分。
4. 在 `${session_dir_rel}/板块候选池.md` 写入：
- 行业资金流三窗口榜单摘要
- 候选池积分表
- 概念催化摘要

### Phase 2: 板块行情与结构采集
对每个候选行业板块，固定调用：
1. `trading_industry_hist_em(symbol, period='日k', adjust='none')`
2. `trading_industry_hist_em(symbol, period='周k', adjust='none')`
3. `trading_industry_hist_em(symbol, period='月k', adjust='none')`
4. `trading_industry_hist_min_em(symbol, period='15')`
5. `trading_industry_cons_em(symbol)`
6. `trading_fund_flow_sector_summary_em(symbol, indicator='今日')`
7. `trading_fund_flow_sector_summary_em(symbol, indicator='5日')`

必须从板块数据中提炼：
- 近 5 日涨跌幅
- 最新收盘相对 20 日均值的偏离
- 日线、周线、月线趋势方向
- 分时强弱与冲高回落风险
- 成份股涨跌分布和龙头集中度

### Phase 3: 龙头股代理分析
1. 每个候选板块固定选 3 只代表股。
2. 代表股筛选顺序固定：
- 先取 `trading_fund_flow_sector_summary_em(symbol, indicator='今日')` 中主力净流入靠前的股票。
- 再与涨幅靠前股票求交集。
- 若交集不足 3 只，再按“主力净流入排序优先、涨幅排序次优先”补足。
3. 对每只代表股固定采集：
- `trading_kline`：`1d/1w/1m`
- `trading_ma(period=5/10/20, ma_type='sma')`
- `trading_macd`
- `trading_rsi(period=14)`
- `trading_volume`
- `trading_fund_flow_individual_em`
4. 必须提炼以下代理信号：
- 是否连续上涨
- 是否量价齐升
- MA5/10/20 是否多头排列
- MACD 是否扩张或死叉
- RSI 是否进入高位过热
- 个股资金流是否与价格同步
5. 将代表股技术和资金流结论拆分写入：
- `${session_dir_rel}/短线板块分析.md`
- `${session_dir_rel}/长线板块分析.md`

### Phase 4: 新闻与催化分析
1. 默认新闻窗口为近 `7` 天；不足时扩展到近 `30` 天，并明确标注“扩窗”。
2. 每个候选板块至少检索三类关键词：
- 板块名
- 3 只代表股名
- 上下游或政策链关键词
3. `stock_news_em` 可用时，优先按“板块名 + 代表股 + 关键词”检索。
4. `stock_news_em` 不可用时，必须联网搜索以下来源：
- 监管机构或部委
- 交易所、上市公司公告
- 主流财经媒体
5. 每条事件必须落表字段：
- 日期
- 事件标题
- 来源
- 类型：`政策监管 / 行业景气 / 企业经营 / 黑天鹅`
- 方向：`利好 / 利空 / 中性`
- 影响期限：`短期 / 中期 / 长期`
- 可信度：`高 / 中 / 低`
- 一句话影响说明
6. 在 `${session_dir_rel}/板块新闻事件.md` 记录所有事件；同类重复报道只记一次。

### Phase 5: 双评分与动作建议
1. 按 `references/scoring-rules.md` 计算每个板块的短线分和长线分。
2. 固定输出四类结果：
- 短线关注 Top5
- 长线关注 Top5
- 潜力观察 Top3
- 回避板块 Top3
3. 固定潜力板块定义：
- 长线分 `>= 70`
- 短线分 `< 60`
- 新闻面净判断为偏多
- 周线和月线结构未破坏
4. 在 `${session_dir_rel}/板块量化评分卡.md` 写入完整评分卡。
5. 在 `${session_dir_rel}/板块分析报告.md` 写入最终详细报告。

## 追高约束
满足以下任意 `2` 条，即标记“禁止追高”：
1. 板块近 `5` 个交易日涨幅 `> 15%`
2. 板块最新收盘偏离 `20` 日均价 `> 12%`
3. 3 只代表股平均 `RSI > 75`
4. 今日资金流强，但 `5日` 和 `10日` 资金流都未进入前 `20`
5. 前 `10` 只成份股中，仅 `1-2` 只贡献主要涨幅

若标记“禁止追高”，短线动作最高只能给 `回踩参与`。

## 数据质量与回退
1. 数据缺失时，必须明确说明，不得补猜。
2. 单个工具失败时：
- 在对应 session 文件记录失败原因
- 标记影响范围
- 使用剩余可用数据继续
3. 若 `stock_news_em` 不可用，必须明确写出“已切换为联网搜索”。
4. 若板块成份股数据不足以选满 3 只代表股，必须说明降级规则。
5. 所有时效信息必须写具体日期。

## 输出约束
1. 全文使用中文。
2. 以投资分析师口吻写作，不使用“可能还行”“看着不错”之类模糊表达。
3. 先讲结论，再给证据。
4. 报告必须同时包含详细报告和简短评分卡两层结果。
5. 严格按 `references/output-format.md` 的标题和字段输出。
