# 参数派生规则

本文件定义参数收集完成后的自动推导逻辑。Producer 在收集完 12 个参数后读取此文件执行推导。

## template 自动推导（用户跳过或选 auto 时）

- 话题含 AI/tech/code/数据/编程/SaaS/digital → `tech-noir`
- 话题含 历史/人物/传记/故事/旅行/vlog → `warm-story`
- 话题含 新闻/评论/分析/政策/时事 → `news-clean`
- 话题含 生活/创意/美食/教程/DIY/时尚 → `pastel-pop`
- 话题含 哲学/思考/文学/心理/冥想 → `minimal-mono`
- 话题含 纪录片/事件/悬疑/战争 → `cinema-drama`
- style=professional → `news-clean`
- style=casual → `pastel-pop`
- style=storytelling → `warm-story`
- 都不匹配 → `tech-noir`（默认）

**template 生效后**：当 template != "none" 时，读取 `skills/video-maker/templates/builtin/{template}.yaml`。模板中的值作为下游参数的默认值。覆盖优先级：**用户显式参数 > 模板预设 > 自动推导默认值**

## lut_style 自动推导（用户跳过或选 auto 时）

- **如果 template 已选定（非 none）**：使用模板中的 `lutStyle` 值
- 否则按话题关键词匹配：
  - 话题含 AI/科技/数据/tech/digital → `tech_cool`
  - 话题含 生活/旅行/时尚/vlog/日常 → `pastel_dream`
  - 话题含 历史/人物/传记/悬疑/drama → `cinematic_drama`
  - style=professional → `news_neutral`
  - style=casual → `docu_natural`
  - style=storytelling → `warm_human`

## 锁定配置（系统硬编码，不可由用户或 agent 修改）

- **字幕**: minimal
- **进度条**: minimal
- **音频波形**: spectrum-bar
- **转场效果**: fade（全片统一）

## BGM/SFX 默认值（不主动询问用户）

- bgm_file: ""（空 = 自动匹配）
- bgm_volume: 0.15
- sfx_enabled: true

## research_depth 自动推导（用户跳过时）

- 1-3min → light
- 3-5min → standard
- 5-10min → deep

## research_depth → 派生参数

| research_depth | depth_searches | depth_min_chars | depth_min_sources |
|---------------|---------------|----------------|-------------------|
| light | 3 | 800 | 2 |
| standard | 6 | 1500 | 4 |
| deep | 10 | 3000 | 6 |
