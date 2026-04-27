# Research Ratify Rules (Layer 1)

Producer 用 Read/Bash 逐条执行以下检查：

## 规则
1. `research.md` 存在且 size > 800 chars
2. 至少 3 个 `##` heading
3. 至少 1 个 URL 引用（http:// 或 https://）— **当 source=local-file 时跳过此规则**

## 执行方式
- 规则 1: `wc -c artifacts/research/run-{N}/research.md`
- 规则 2: `grep -c "^## " artifacts/research/run-{N}/research.md`
- 规则 3: 如果 goal.yaml 中 source != local-file，则 `grep -c "https\?://" artifacts/research/run-{N}/research.md`；source=local-file 时自动 pass

- id: data-points-table
  description: "Data Points Table 至少 3 行且每行有 source"

## 通过条件
所有规则通过 → Layer 1 pass → 进入 Layer 2（Reviewer agent）
任一失败 → Layer 1 fail → 直接进入重试流程（不执行 Layer 2）
