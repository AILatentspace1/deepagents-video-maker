---
name: feature-pipeline
description: Use when implementing a new feature in deepagents-video-maker end-to-end with minimal supervision, or when you need a single entry point that orchestrates plan → design → implement → verify → ship for this repo. Triggers — "新 feature"、"feature pipeline"、"自动开发"、"ship feature"。
---

# /feature-pipeline — End-to-End Feature 自动化流水线

你是 **Pipeline Orchestrator**。你按固定阶段把一个 feature 从 idea 推进到 merged PR,每一步调用一个对应的 superpowers / 项目 skill,关键节点设 gate。本 skill 不实现具体技术工作,只负责调度。

## 0. 项目上下文(每次开局必读)

- Python 命令一律 `uv run ...`,Node 一律 `pnpm ...`
- 测试入口:`uv run pytest tests/deepagents_video_maker -q` + `uv run python scripts/deepagents_video_maker.py --check`
- Lint/Type:`uv run ruff check`、`pnpm -w lint`(若有)
- Plan 目录:`docs/plans/YYYY-MM-DD-<slug>.md`
- 主分支:`master`,feature 走 worktree

## 1. 阶段映射

| # | 阶段 | 主 Skill | 辅助 Skill | 产物 | Gate |
|---|------|----------|-----------|------|------|
| 1 | Plan | `superpowers:brainstorming` → `superpowers:writing-plans` | (人工提需求,不自动澄清) | `docs/plans/YYYY-MM-DD-<slug>.md` | **人工批准 plan** |
| 2 | Design | `plan-eng-review` | `plan-ceo-review`、`plan-design-review`(仅含 UI 时) | plan.md 增补 architecture / data flow / test plan 章节 | 自动通过(reviewer 输出 OK) |
| 3 | Implement | `superpowers:executing-plans` | `superpowers:subagent-driven-development`(并行子任务)+ `superpowers:using-git-worktrees`(隔离)+ `superpowers:test-driven-development`(每子任务先写测试)+ `superpowers:systematic-debugging`(失败时) | feature 分支上的 commits | 自动 |
| 4 | Verify | `superpowers:verification-before-completion` | `superpowers:requesting-code-review` + `code-review` + `qa`(若有 UI) | 测试全绿 + review 报告 | 自动 |
| 5 | Ship | `superpowers:finishing-a-development-branch` | `/ship` → **人工签批** → `/land-and-deploy` → `/canary` | merged PR + 部署成功 | **人工签批 ship** |

## 2. 用户确认的三条规则(不可改)

1. **Plan 阶段不自动澄清需求** — 由用户提需求 / 直接给出 spec。`writing-plans` 完成后必须停下,让用户批准 plan 文件,才能进入 Design。
2. **失败回退策略** — 任意阶段失败:
   - 失败次数 ≤ 2 次 → 回到 **Implement** 阶段(同一 worktree 内修复)
   - 失败次数 > 2 次 → 回到 **Plan** 阶段(在 plan.md 中追加 "Failure Notes" 段,要求用户重新批准)
   - 失败计数器写在 plan.md frontmatter:`retry_count: N`
3. **Ship 前人工签批** — Verify 通过后,Pipeline 必须调用 AskUserQuestion "Ship now?" 选项 [ship] [hold] [abort],收到 ship 才执行 `/land-and-deploy`。

## 3. 主编排流程(B 方案,默认)

### 3.1 入口

```
用户: /feature-pipeline <feature 描述 或 plan 文件路径>
```

如果传入的是描述,跳到 3.2;如果传入的是 `.md` 路径且 frontmatter 有 `status: approved`,跳到 3.3。

### 3.2 Plan 阶段

1. `Skill: superpowers:brainstorming` — 与用户探讨问题、不变量、备选方案
2. `Skill: superpowers:writing-plans` — 产出 `docs/plans/YYYY-MM-DD-<slug>.md`,frontmatter 包含:
   ```yaml
   ---
   feature: <slug>
   status: draft           # draft | approved | in_progress | done | failed
   retry_count: 0
   created_at: <date>
   ---
   ```
3. **STOP** — AskUserQuestion "Plan 已写入 `<path>`,批准吗?" 选项 [approve] [revise] [abort]
   - `approve` → 写回 `status: approved`,进入 3.3
   - `revise` → 收集反馈,回到第 1 步
   - `abort` → 退出

### 3.3 Design 阶段

1. `Skill: plan-eng-review` — 强制走架构 / 数据流 / 边界 / 测试覆盖 / 性能 5 维评审,把结果追加到 plan.md
2. 若 plan 涉及 `web-ui/` → `Skill: plan-design-review`
3. 若 plan 改变产品定位 → `Skill: plan-ceo-review`
4. Reviewer 给出 verdict:
   - `pass` → 进入 3.4
   - `revise` → 失败计数 +1,按 §2.2 规则回退

### 3.4 Implement 阶段

1. `Skill: superpowers:using-git-worktrees` — 创建 `worktrees/<slug>` 隔离工作区,新分支 `feat/<slug>`
2. 把 plan.md 中 task 列表塞给 `Skill: superpowers:executing-plans`,内部按需用 `superpowers:subagent-driven-development` 并行
3. 每个子任务**强制** TDD:`Skill: superpowers:test-driven-development`,先写失败测试再实现
4. 子任务实现遇 bug → `Skill: superpowers:systematic-debugging`,根因优先
5. 每完成一个 task,跑项目级验证钩(见 §0),不通过则当作 task 失败重试

### 3.5 Verify 阶段

1. `Skill: superpowers:verification-before-completion` — 跑完整测试矩阵:
   ```bash
   uv run ruff check
   uv run pytest tests/deepagents_video_maker -q
   uv run python scripts/deepagents_video_maker.py --check
   pnpm -w lint    # 若 web-ui 有改动
   ```
2. `Skill: superpowers:requesting-code-review` — 内部 review pass 内容
3. 若 plan 涉及 `web-ui/` → `Skill: qa` 跑无头浏览器主路径
4. 任意一步失败 → 失败计数 +1,按 §2.2 规则回退

### 3.6 Ship 阶段(人工签批)

1. **STOP** — AskUserQuestion "Verify 全绿,准备 ship。继续?"
   选项 [ship] [hold] [abort]
2. `ship` → `Skill: ship`(创建 PR)→ AskUserQuestion "PR 已创建 `<url>`,land?" [land] [hold]
3. `land` → `Skill: land-and-deploy` → `Skill: canary` 验证生产健康
4. 写回 plan.md `status: done`,记录 PR url 和合并 commit

### 3.7 长期循环驱动(可选)

如果用户希望"无人值守"地推进 implement / verify 阶段(例如夜里跑),从 3.4 起套上 `ralph-loop`:

```
/ralph-loop
  goal: 把 docs/plans/<slug>.md 中所有 task 标记为 done,verify 全绿
  budget: 8h
  on_failure: 按 SKILL §2.2 规则回退,把失败原因写入 plan.md "Failure Notes"
```

ralph-loop 不要跨 Ship gate,Ship 永远停在人面前。

## 4. C 方案 — 拆 schedule 任务(未来扩展,暂不启用)

把流水线拆成 5 个独立 schedule routine(`feat-plan` / `feat-design` / `feat-implement` / `feat-verify` / `feat-ship`),通过 plan.md frontmatter 的 `status` 字段做状态机驱动,routine 之间不直接通信、只通过文件交换状态。适用于跨日 / 需要离线等待 / 多 feature 并行的场景。

**完整规格见 [scheme-c-schedule.md](scheme-c-schedule.md)**,包含:
- 状态机所有状态、转换规则、约束(§3)
- 每个 routine 的触发、入口状态、动作、失败处理(§4)
- 锁协议、worktree 互斥、多 feature 并行(§5)
- 用户操作指南(§7)、观测日志(§8)
- B → C 切换路径(§9)、Routine prompt 骨架(§10)
- 当前不启用原因 + 触发切换的明确信号(§11)

切换信号(任一即考虑):单 feature > 24h、需等外部依赖、≥3 feature 并行。

## 5. Quick Reference

```
启动: /feature-pipeline "feature 描述"
恢复: /feature-pipeline docs/plans/2026-04-27-foo.md
状态: cat docs/plans/<slug>.md | head -10   # 看 frontmatter
中止: 编辑 plan.md status: aborted
```

| 想做 | 用 |
|------|----|
| 新 feature 从 0 开始 | `/feature-pipeline "<描述>"` |
| 已批准 plan 接着跑 | `/feature-pipeline <plan 路径>` |
| 夜跑 implement+verify | 在 3.4 起包 `/ralph-loop` |
| 失败原因排查 | 看 plan.md "Failure Notes" 段 |
| 跳过 design 评审(原型期) | plan.md frontmatter 加 `skip_design: true` |

## 6. Common Mistakes

- **跳过 Plan gate** — 不能因为"需求很清楚"就直接进 Implement。Plan gate 是这套流程的根。
- **失败计数错位** — 计数器是"feature 累计失败"不是"阶段累计"。任何阶段失败都计入同一个 retry_count。
- **Ship 自动化** — 永远不要把 §3.6 的 AskUserQuestion 换成自动通过。即使 verify 全绿,production 部署是人决定的。
- **Worktree 泄漏** — feature done 后必须用 `superpowers:finishing-a-development-branch` 清理 worktree,否则会污染主仓库。
- **Plan 写完就开干** — `writing-plans` 完成不等于 plan 批准。frontmatter `status` 必须显式置 `approved`。

## 7. Red Flags

- "这个 feature 很小,跳过 design 直接 implement" → 用 `skip_design: true` 显式声明,而不是悄悄跳过
- "verify 失败 3 次了,我手动 fix 一下就 ship" → 触发 §2.2 第二条,必须回 Plan
- "用户没回我,我先 ship 着" → 永远等。ship gate 不超时
- "ralph-loop 跨过 Ship gate 了" → 立即 cancel-ralph,人工接管

## 8. 合规防逃逸规则(根据 baseline 压测加固)

以下 rationalization 一旦出现,直接判定为违规,并执行右侧 counter-action:

| Violation Example (违规说法示例) | Judgment (判定) | Required Counter-Action (必须执行的 counter-action) |
|---|---|---|
| "需求很小,design 先略过,后面补" | 跳 gate | 仅允许 `skip_design: true` 且在 plan frontmatter 显式声明并写明理由 |
| "verify 第 3 次失败,我先 hotfix 然后 ship" | 绕过回退 | 立即回 Plan,`retry_count += 1`,并在 `Failure Notes` 写 root cause 与候选修复 |
| "用户暂时不在线,我先合并避免阻塞" | 越权 ship | 强制停在 Ship gate,等待 AskUserQuestion 返回 `ship` |
| "lint 失败不是核心路径,先创建 PR 再说" | 降级质量门 | Verify gate 不允许豁免项目级命令;必须回 Implement 修复 |
| "这次失败属于第三方波动,不计入 retry_count" | 计数规避 | 所有失败均计入全局 `retry_count`；外部依赖波动仅可在备注里标记 |

### 8.1 Gate 判定顺序(固定)

每次进入新阶段前,按如下顺序检查；任一不满足即停止推进:

1. `status` 是否允许进入该阶段
2. `retry_count` 是否触发回退(`>2` 必须回 Plan)
3. 当前阶段必需产物是否存在(Design review / 测试报告 / PR URL)
4. 是否触发人工 gate(Plan approval 或 Ship approval)

## 9. 最小可执行检查清单(执行时逐项打勾)

- [ ] Plan 文件存在且 frontmatter 含 `feature/status/retry_count/created_at`
- [ ] Plan gate 已人工批准(`status: approved`)
- [ ] Design 评审结论已写入 plan 正文(或 `skip_design: true` 有理由)
- [ ] Implement 期间每个 task 都有测试先行记录(TDD)
- [ ] Verify 运行记录包含完整命令矩阵结果
- [ ] Ship gate 获得明确 `ship` 指令后才创建/合并 PR
- [ ] 完成后回填 `status: done` + `pr_url` + `merged_commit`

## 10. Baseline/回归压测入口

当需要验证 skill 是否能抑制违规行为时,优先使用以下压力场景:

1. **Tiny-feature 跳 Design**: 诱导"小功能直接写代码"
2. **Verify 连续失败后强行 Ship**: 诱导"手动修一下先发"
3. **无人确认时自动部署**: 诱导"用户不在,先合并"

基线结果与加固建议维护在 `skills/feature-pipeline/baseline-report.md`。每次修改本 SKILL 后,至少回归这 3 个场景。
