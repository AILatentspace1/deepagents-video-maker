# Script Ratify Rules (Layer 1)

## 规则
1. `script.md` 存在
2. scene 数量在目标范围内（按 duration 查表）
3. 无连续 3 个以上同类型 scene
4. 每个 narration/data_card/quote_card scene 有 `narration:` 字段
5. narration、data_card、quote_card 场景必须包含 `scene_intent` 和 `content_brief`（codegen 必填）
6. narration、data_card、quote_card 场景禁止包含 `layer_hint` 或 `beats`（已废弃）
7. data_card 场景必须包含 `data_semantic` 且 `items` 非空
8. narration 场景禁止包含 `data_semantic` 字段（仅 data_card 允许）

## 执行方式
- 规则 1: `test -f artifacts/script/run-{N}/script.md`
- 规则 2: `grep -c "^## Scene" artifacts/script/run-{N}/script.md`，对比数量表
- 规则 3: 解析 scene type 序列，检查连续同类型不超过 3
- 规则 4: 对每个有旁白的 scene，grep `narration:`
- 规则 5: 对每个 narration/data_card/quote_card scene，检查是否包含 `scene_intent:` 和 `content_brief:`
- 规则 6: 对每个 narration/data_card/quote_card scene，检查不包含 `layer_hint:` 或 `beats:`
- 规则 7: 对每个 data_card scene，检查是否包含 `data_semantic:` 且 `items:` 非空
- 规则 8: 对每个 narration scene，检查不包含 `data_semantic:`

## 通过条件

### eval_mode == "gan"
所有 Layer 1 规则通过 → 跳过 Layer 2 Reviewer → 由 Evaluator 替代（见 `milestones/script.md` Phase 4）

### eval_mode != "gan"（legacy）
所有 Layer 1 规则通过 → 进 Layer 2 Reviewer | 任一失败 → 重试
