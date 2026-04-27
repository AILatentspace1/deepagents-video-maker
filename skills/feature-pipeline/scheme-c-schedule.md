# 方案 C — Schedule Routine 拆分流水线(详细规格)

> 状态:**草稿,未启用**。当前默认走方案 B(SKILL.md §3)。本文档定义将来需要切换到 C 时的完整规格。

## 1. 设计动机

方案 B 把整条 plan→ship 流水线塞在一个会话里运行,要求:
- 一直有人或 ralph-loop 在线
- 单个 feature 在合理时间内能跑完(< 24h)
- 不需要等待外部异步事件

当现实违反任一条件时,会话级编排会退化成"停在某一步等",浪费上下文窗口和注意力。方案 C 把每阶段拆成独立 routine,通过文件状态机协作,每个 routine 启动时检查状态、做一步、写回状态、退出 — 真正的离线驱动。

### 1.1 适用场景

满足以下任一即考虑切换到 C:

| 触发条件 | 例子 |
|----------|------|
| 单 feature 平均 > 24h | 涉及大模型训练、数据回流、外部供应商响应 |
| Implement 阶段需要等待外部依赖 | 等人工标注、第三方 API rate limit、白名单审批 |
| 多 feature 并行 | 同时推 3+ 个 feature,每个进度不一 |
| 跨时区协作 | 设计/产品在另一时区批 plan,实现可在夜里跑 |

### 1.2 不适用场景

- 一次性 PoC、bugfix、文档改动 → 直接 B 方案
- feature 全程 < 4h → routine 调度开销不划算
- 没有可信 CI / 测试覆盖 → 自动化没有兜底,失败会放大

## 2. 整体架构

```
┌──────────────────────────────────────────────────────────────────────┐
│  docs/plans/<slug>.md  ←── 单一事实源(状态 + 任务 + 失败记录)        │
└──────────────────────────────────────────────────────────────────────┘
        ▲                ▲                ▲                ▲
        │                │                │                │
   ┌────┴────┐      ┌────┴─────┐    ┌─────┴─────┐    ┌─────┴─────┐
   │feat-plan│ ───> │feat-     │──> │feat-      │──> │feat-      │──> [ship gate]
   │(on-     │      │design    │    │implement  │    │verify     │       │
   │ demand) │      │(1h cron) │    │(30m cron) │    │(1h cron)  │       ▼
   └─────────┘      └──────────┘    └───────────┘    └───────────┘   ┌──────────┐
                                          │                          │feat-ship │
                                          │ uses                     │(on-      │
                                          ▼                          │ demand)  │
                                    ┌──────────┐                     └──────────┘
                                    │ worktrees│
                                    │ /<slug>/ │
                                    └──────────┘
```

每个 routine 是独立的远程 agent,它们之间**不直接通信**,只通过两份共享物:
- **plan.md**:状态机驱动 + 任务清单 + 失败记录
- **worktree** `worktrees/<slug>`:代码工作区,git 分支 `feat/<slug>`

## 3. plan.md 状态机

### 3.1 完整 frontmatter schema

```yaml
---
# 标识
feature: <slug>                 # kebab-case,< 30 字符
created_at: 2026-04-27T14:00:00+08:00
owner: <github-handle>          # 谁负责签批

# 状态机(核心)
status: draft                   # 见 3.2
status_history:                 # 状态转换审计
  - { ts: ..., from: draft, to: pending_approval, by: feat-plan }
  - { ts: ..., from: pending_approval, to: approved, by: human }
locked_by: null                 # 当前持有写锁的 routine 名;null 表示空闲
locked_at: null

# 失败计数
retry_count: 0                  # 跨阶段累计
last_failure:
  stage: verify
  reason: "pytest deepagents_video_maker/test_agent.py::test_foo failed"
  ts: ...

# 工作区
worktree_path: worktrees/<slug>
branch: feat/<slug>

# 配置开关
skip_design: false
skip_qa: false                  # 无 UI 改动可跳过
quality_threshold: standard     # standard | strict

# 产物
pr_url: null                    # ship 完成后填
merged_commit: null

---
```

### 3.2 状态枚举与转换

| 状态 | 含义 | 谁能写入 | 下一可达状态 |
|------|------|----------|--------------|
| `draft` | 由 feat-plan 写入草稿,等用户批 | feat-plan | `pending_approval` |
| `pending_approval` | plan 写完,等用户人工批准 | feat-plan | `approved`(人) / `aborted`(人) |
| `approved` | 用户批了,等 feat-design 拉取 | human / 系统(回退时) | `designing`(feat-design 启动) / `aborted` |
| `designing` | feat-design 运行中(临时态) | feat-design | `designed` / `revise_needed` / `failed` |
| `designed` | 设计评审通过,等 feat-implement | feat-design | `implementing` |
| `implementing` | feat-implement 运行中 | feat-implement | `implemented` / `revise_needed` / `failed` |
| `implemented` | 所有 task 完成,等 feat-verify | feat-implement | `verifying` |
| `verifying` | feat-verify 运行中 | feat-verify | `verified` / `revise_needed` / `failed` |
| `verified` | verify 全绿,等用户签批 ship | feat-verify | `shipping`(用户触发) / `aborted` |
| `shipping` | feat-ship 运行中 | feat-ship | `done` / `failed` |
| `done` | 已 merge + 部署成功 | feat-ship | (终态) |
| `revise_needed` | 当前阶段失败,等回退处理 | 任意 routine | `approved`(<=2) / `draft`(>2) |
| `failed` | 不可恢复(罕见) | 任意 routine | (终态,需人工介入) |
| `aborted` | 用户中止 | human | (终态) |

### 3.3 转换规则约束

- `*-ing` 是临时态,routine 退出前必须转出。如 routine 异常崩溃留下 `*-ing`,下次启动时检测到 `locked_at` 超过 30 分钟,自动 unlock 并重新进入。
- `aborted`、`done`、`failed` 是终态,任何 routine 检测到立即退出。
- `revise_needed` 是回退枢纽:
  - retry_count <= 2 → 自动写回 `approved`(轻度回退,重新走 design+implement+verify)
  - retry_count > 2 → 写回 `draft`(重度回退,要求用户改 plan 或追加约束),并把失败原因写入 plan.md 正文 "Failure Notes" 段

## 4. 各 Routine 详细规格

每个 routine 启动时的固定开场白:
```
1. 锁:CAS 把 plan.md 的 locked_by 从 null 改成自己;失败立即退出
2. 状态匹配:不在自己的触发状态里 → 解锁,退出
3. 转入 *-ing 状态,记录 status_history
4. 干活
5. 转出 *-ing 到 next/error 状态,记录
6. 解锁,退出
```

### 4.1 `feat-plan`

| 字段 | 值 |
|------|----|
| 触发 | on-demand(用户跑 `/schedule run feat-plan --plan <slug>`) |
| 入口 status | `draft` 或不存在 |
| 用 Skill | `superpowers:brainstorming` → `superpowers:writing-plans` |
| 输入 | 用户给的 feature 描述(命令行参数) |
| 输出 | `docs/plans/<date>-<slug>.md`,frontmatter `status: pending_approval` |
| 失败处理 | 写 `status: failed`,正文记录失败原因 |
| 不做 | 不写代码,不动 worktree |

注:`writing-plans` 完成后**不再询问用户**,直接停在 `pending_approval`,等用户在另一个会话里把 status 改成 `approved`(或者用 `feat-approve` 辅助命令一行改)。

### 4.2 `feat-design`

| 字段 | 值 |
|------|----|
| 触发 | cron `0 * * * *`(每小时 0 分) |
| 入口 status | `approved` |
| 用 Skill | `plan-eng-review`(必),`plan-design-review`(若 plan 涉及 web-ui),`plan-ceo-review`(若 plan 改产品定位) |
| 动作 | 加锁 → 状态转 `designing` → 跑评审,把结果**追加**到 plan.md 正文 "Design Review" 段 → 评分通过(各维度 ≥ 7/10)则转 `designed`,否则 `revise_needed` 并 retry_count +1 |
| 失败处理 | 评审报错(非评分低)→ `failed` |
| 幂等性 | 若 plan.md 已存在 "Design Review" 段且时间戳在 24h 内,跳过,直接转 `designed` |

### 4.3 `feat-implement`

| 字段 | 值 |
|------|----|
| 触发 | cron `*/30 * * * *`(每 30 分) |
| 入口 status | `designed` 或 `implementing`(续跑) |
| 用 Skill | `superpowers:using-git-worktrees`(首次)、`superpowers:executing-plans`、`superpowers:test-driven-development`、`superpowers:systematic-debugging` |
| 动作 | 加锁 → 状态转 `implementing` → 检查 worktree,不存在则创建 → 取 plan.md 任务清单中第一个未完成 task → TDD 实现 → 提交 → 跑项目级 lint/test → 标 task 完成 → 若所有 task 完成则状态转 `implemented`,否则保持 `implementing` 等下次 tick |
| 单次 tick 时间盒 | 最多 25 分钟,超时强制保存进度后退出(避免下次 tick 撞车) |
| 失败处理 | 单 task 失败 ≤ 2 次 → 下次 tick 重试同一 task;> 2 次 → 状态转 `revise_needed`,retry_count +1 |
| 关键约束 | 必须 `git push` 推到远程的 `feat/<slug>` 分支,让其他 routine / 用户能看到进度 |

### 4.4 `feat-verify`

| 字段 | 值 |
|------|----|
| 触发 | cron `30 * * * *`(每小时 30 分,与 feat-design 错开) |
| 入口 status | `implemented` |
| 用 Skill | `superpowers:verification-before-completion`、`superpowers:requesting-code-review`、`code-review`、`qa`(若 web-ui 有改动) |
| 动作 | 加锁 → 状态转 `verifying` → 在 worktree 里跑完整验证矩阵 → 全绿则转 `verified`,任意一项失败转 `revise_needed` 并 retry_count +1 |
| 验证矩阵 | `uv run ruff check` + `uv run pytest tests/deepagents_video_maker -q` + `uv run python scripts/deepagents_video_maker.py --check` + `pnpm -w lint` + `qa`(条件触发) |
| 失败记录 | 失败详情写入 plan.md "Verify Run #N" 段 |

### 4.5 `feat-ship`

| 字段 | 值 |
|------|----|
| 触发 | on-demand,**用户手动触发**(`/schedule run feat-ship --plan <slug>` 或 RemoteTrigger 信号) |
| 入口 status | `verified` |
| 用 Skill | `superpowers:finishing-a-development-branch`、`/ship`、`/land-and-deploy`、`/canary` |
| 动作 | 加锁 → 状态转 `shipping` → 确认 frontmatter `owner` 字段与触发用户匹配(防误触)→ 创建 PR → 轮询 CI → merge → 部署 → canary 通过 → 状态转 `done`,写入 `pr_url` 和 `merged_commit` |
| 失败处理 | 任意一步失败 → `failed`(不自动重试,人工介入) |
| 关键约束 | **绝不能放在 cron 上**。把 ship 设成定时任务等于把生产部署交给时钟,违反"ship 前人工签批"。 |

## 5. 并发与互斥

### 5.1 锁协议

plan.md frontmatter `locked_by` 是软锁,基于乐观并发控制:

1. routine 启动后读 plan.md
2. 如果 `locked_by != null`:
   - 检查 `locked_at`,若 > 30 分钟则视为僵死锁,强制解锁并继续
   - 否则退出(下次 cron 再试)
3. 写入 `locked_by: <self>, locked_at: <now>`,**带 git commit**(.md 落盘)
4. 干活
5. 退出前清空锁,git commit

由于 plan.md 在 git 里,push/pull 即天然 CAS:推时若上游已变,routine 退出。

### 5.2 worktree 互斥

同一 worktree 同时只能有一个 routine 操作。`feat-implement` 是唯一的写入者,其他只读。`feat-verify` 在 verify 期间不修改代码,只跑命令。

### 5.3 多 feature 并行

每个 feature 独立 plan.md + worktree,routine 启动时扫描 `docs/plans/*.md`,只处理 status 命中自己的那些。多个 feature 同时进入 implement 不冲突(不同 worktree)。

## 6. 错误处理与回退

### 6.1 阶段失败回退路径

```
            ┌──────────────────────────────────────────┐
            │                                          │
            ▼                                          │
   ┌──────────────┐    retry+1 <=2    ┌─────────────┐  │
   │ revise_needed│ ─────────────────>│  approved   │──┘
   └──────────────┘                   └─────────────┘
            │ retry+1 >2
            ▼
   ┌──────────────┐
   │    draft     │  ← 写入 "Failure Notes",等用户改 plan
   └──────────────┘
```

### 6.2 不可恢复错误(`failed`)

下列情况直接 `failed`,不自动回退:
- worktree 损坏(git 状态混乱无法清理)
- ship 失败(merge 冲突 / CI 红 / 部署失败)
- routine 崩溃 3 次以上(连续锁超时被强制解锁)

`failed` 后所有 routine 跳过这个 plan,等人工介入。

### 6.3 用户中止

任何时候,把 plan.md frontmatter 改成 `status: aborted` 即可。下次 routine 启动检测到立即退出。

## 7. 用户操作指南(将来启用后)

### 7.1 启动一个 feature

```bash
# 1. 写 plan
/schedule run feat-plan --feature "新需求描述"
# 等 routine 完成,plan.md status = pending_approval

# 2. 审 plan(在 IDE 里读)
$EDITOR docs/plans/2026-04-27-foo.md

# 3. 批准
/schedule run feat-approve --plan docs/plans/2026-04-27-foo.md
# 这是辅助 routine,只改 status: pending_approval -> approved

# 4. 然后什么都不用做,cron routine 自动推进 design / implement / verify
```

### 7.2 看进度

```bash
# 看所有进行中的 plan
ls docs/plans/*.md | xargs head -15 | grep -E '^(feature|status):'

# 看某个 feature 详情
cat docs/plans/2026-04-27-foo.md
```

### 7.3 ship

```bash
# verify 完成后,plan.md status = verified
# 用户手动触发(等于按下"发布"按钮)
/schedule run feat-ship --plan docs/plans/2026-04-27-foo.md
```

### 7.4 干预

| 想做 | 怎么做 |
|------|--------|
| 暂停某 feature | 改 status: aborted(可以再改回来,但 retry_count 不会重置) |
| 跳过 design 评审 | 在 frontmatter 加 `skip_design: true`,feat-design 看到直接转 `designed` |
| 强制重跑 verify | 改 status: implemented |
| 加新任务 | 编辑 plan.md task 列表,即使 status 已是 implementing 也行(routine 下次 tick 会发现新 task) |

## 8. 观测与日志

每个 routine 把 stdout/stderr 写到:
```
docs/plans/<slug>.logs/
  feat-plan-<ts>.log
  feat-design-<ts>.log
  feat-implement-<ts>.log
  ...
```

不要存到 `worktrees/`,因为 worktree 会被删。`docs/plans/` 进 git。日志文件超过 10 MB 自动 truncate(保留首尾各 5 MB)。

## 9. 切换路径(B → C)

切换是单向的,且**只对新 feature 生效**(进行中的 feature 继续走 B 直到 done)。步骤:

1. **建 routine**:用 `Skill: schedule` 分别创建 5 个 routine(prompt 模板见 §10),先全部 `paused`
2. **冷启动 dry-run**:挑一个低风险 feature,手动一次次触发 `/schedule run feat-* --plan ...`,确认每个 routine 行为正确、状态机流转无误
3. **开 cron**:把 feat-design / feat-implement / feat-verify 三个改成 `active`,观察 24h
4. **切换 SKILL.md 默认**:在 [skills/feature-pipeline/SKILL.md](SKILL.md) 把"默认走 §3"改成"默认走 §4",并把 §3(B 方案)标记为"快速通道,适合小改动"
5. **保留 B 方案**:不删除,因为小 feature 直接 B 更快

## 10. Routine prompt 模板(预留)

每个 routine 是独立 agent,prompt 必须自包含。骨架:

```
你是 deepagents-video-maker 项目的 <ROUTINE-NAME> routine。

每次唤醒,严格执行:
1. 扫描 docs/plans/*.md,过滤 frontmatter status == "<MY-TRIGGER-STATUS>"
2. 对每个匹配的 plan:
   a. 尝试加锁(CAS locked_by),失败则跳过
   b. 状态转 <MY-RUNNING-STATE>,git commit + push
   c. 调用 Skill <MY-PRIMARY-SKILL>,按 SKILL.md §<SECTION> 执行
   d. 根据结果转出状态(<NEXT-STATE> / revise_needed / failed)
   e. 解锁,git commit + push
   f. 把日志保存到 docs/plans/<slug>.logs/<routine>-<ts>.log
3. 退出

若任意步骤异常,转 failed,在 plan.md 正文记录 traceback,解锁退出。
绝不调用 Ship gate 后的任何 skill。
```

具体 5 个 routine 的 prompt 在切换时再展开,不预先写,避免分叉漂移。

## 11. 当前不启用的原因

1. 这个 repo 单 feature 周期通常 < 1 天,B 方案足够
2. cron 调度需要 `/schedule` 权限和环境,本地开发态没必要
3. 还没建立"plan.md 是单一事实源"的习惯,直接上分布式状态机会乱
4. 第一个 feature 还没用 B 方案验证过,谈优化太早

**触发切换的明确信号**:有一个 feature 跑了 36 小时还没 ship,或者同时有 ≥3 个 feature 在不同阶段卡住。看到任一信号,回到 §9 切换。
