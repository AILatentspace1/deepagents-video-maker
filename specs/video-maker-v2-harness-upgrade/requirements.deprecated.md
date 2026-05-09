# 需求文档 — video-maker-v2 Harness Upgrade (v2.1)

## 介绍

本次升级（v2.1）参考 [`ConardLi/garden-skills/skills/web-video-presentation`](https://github.com/ConardLi/garden-skills/tree/main/skills/web-video-presentation) 的成熟方法论，把当前 video-maker-v2（Remotion 输出路线）从"脚本驱动单线程渲染"升级为"内容/视觉双轨 + 主题系统 + 章节隔离 + 独立审查"的工程化流程。

**根本约束**：本次仍保留 Remotion 渲染路线（不切换到网页 + 屏幕录制）。`web-video-presentation` 中"全局 step 计数器 + Auto 模式录屏"等强依赖网页运行时的部分，**翻译为 Remotion 原生等价物**：

| web-video-presentation 概念 | video-maker-v2 v2.1 等价物 |
|---|---|
| 全局 `step` 计数器 + 点击推进 | 章节内 `<Sequence>` 链，`durationInFrames` 由 narrations 推导 |
| `narrations.ts` 单一真相源 | 每章 `narrations.ts` 同时驱动 audio synthesis + scene 数量 + 字幕 |
| Auto 模式录屏 | Remotion deterministic render（已天然同步） |
| `tokens.css` + primitive class | `theme.ts` + primitive 组件（`<HeroNum>` / `<Rule>` / `<Card>` / `<StageFrame>`） |
| Vite + React 项目 | Remotion 项目（仍是 React，但 Composition 输出） |

**升级范围**（按工作流阶段组织）：

| 分组 | 需求编号 | 内容 |
|---|---|---|
| 清理 | 0 | 移除 better-harness 基础设施 |
| 内容 Phase 1 | 1, 2, 3, 4 | 双源原则 + 脚本风格强化 + outline.md + chapters 契约 |
| 协作节点 | 5, 6, 7 | 5-in-1 Checkpoint + 主题系统 + 3 种开发模式 |
| 视觉 Phase 2 | 8, 9, 10 | 第 1 章基准 + narrations 真相源 + 章节物理隔离 |
| 独立审查 | 11 | Reviewer Agent + 修复后汇报铁律 + 三层降级 |
| 配置/兼容 | 12, 13 | goal.yaml/state.yaml 扩展 + v2.0 兼容 |

兼容策略：版本号从 v2 升至 v2.1，新流程默认启用，旧输出目录通过兼容层保留。better-harness 移除属于一次性 breaking change，不保留兼容层。

---

## 需求

### 需求 0 - 移除 better-harness 基础设施

**用户故事：** 作为维护者，我希望移除已无实际优化信号的 better-harness 基础设施，避免它持续占用文档篇幅、误导代理认为该路径仍可用，并为 v2.1 引入的 Reviewer Agent 让出反馈源位置。

**背景信号断链证据：**
- `harness/video-maker-minimal.toml` 唯一可优化 surface 是 `skills/video-maker-v2/agents/scriptwriter.md`
- 但其全部 7 个 `[[cases]]` 引用的测试均为合成输入的 ratify 单元测试或文件存在性测试，不调用 LLM、不读取 `scriptwriter.md`
- 因此对 `scriptwriter.md` 的任何 mutation 都不能改变 case 通过率，优化器在真空中迭代

#### 验收标准

1. The 仓库 shall 不再包含 `harness/` 目录及其 5 个文件。
2. The 仓库 shall 不再包含 `scripts/run-harness.ps1`。
3. The `runs/` 目录 shall 被删除。
4. The `package.json` 的 `scripts` 块 shall 删除 `harness:validate` 与 `harness:run` 两个条目。
5. The `CLAUDE.md`（项目根级）shall 删除 "Better-Harness (scriptwriter-only)" 章节。
6. The `tests/deepagents_video_maker/test_skill_files.py` 中的 `test_harness_and_package_scripts_do_not_reference_removed_v1_or_evals` shall 替换为 `test_better_harness_infrastructure_removed`，断言 `harness/` 与 `harness:*` script 均不存在。
7. When 用户运行 `pnpm test:py` 与 `uv run pytest tests/deepagents_video_maker -q`, the 测试套件 shall 全部通过。
8. The `README.md`、其他根级文档及 `docs/` 中如有 better-harness 引用 shall 一并清理。
9. 移除 commit shall 在 commit message 中显式说明信号断链证据。
10. 本次移除 shall 不保留兼容层、不提供回滚开关。

---

### 需求 1 - 双源原则与 article.md 保留

**用户故事：** 作为视频制作者，我希望流程严格执行"双源原则"——`script.md` 决定节拍/顺序，`article.md` 决定画面信息密度——并保留原始文章作为 Remotion Builder 实现期的细节源，使屏幕信息密度高于口播信息密度，避免画面沦为"口播稿打字稿"。

#### 验收标准

1. When 用户提供原始文章（`source: local-file | folder | manual` 且包含可读文章文本）, the Producer shall 在 Setup 阶段将该文章落盘为 `{output_dir}/article.md`，并在整个 workflow 全程保留不删除。
2. When 用户直接提供口播稿（无原始文章）, the Producer shall 跳过 `article.md` 创建并在 `state.yaml` 中记录 `dual_source_mode: script_only`，告诉下游代理走"画面装饰元素池"退化路径。
3. The `article.md` shall 不参与 ratify 检查（它是细节源不是契约工件），但其存在状态 shall 记录在 `state.yaml.dual_source_mode` 中。
4. When Scriptwriter 派发任务, the Producer shall 显式传入 `{article_file}` 路径（若存在），让 Scriptwriter 同时持有 article 与 source-manifest。
5. When Remotion Builder 派发任务, the Producer shall 在 boundaries 中显式传入 `{article_file}` 路径并要求 Builder 在实现每章时**回读 article.md 对应段落**抽取细节挂到画面。
6. The Reviewer 项目清单 shall 包含核查项 `project.screen_density_above_narration` —— 抽样几个 scene 验证画面信息密度高于口播文本密度（不是把 narration 打字打了一遍）。
7. While `article.md` 存在 but 用户未启用 dual-source mode（设置 `dual_source_mode: script_only`）, the Producer shall 警告但不阻断；这是 escape hatch。

---

### 需求 2 - SCRIPT-STYLE 强化（信息保留度 + 去 AI 味）

**用户故事：** 作为内容质量负责人，我希望 Scriptwriter 在生成 `script.md` 时遵循**信息保留度 ≥ 60%** 与"去 AI 味五类"的硬性规范，使口播稿在念出来时不像机器，而像真人聊天，同时关键信息不丢失。

#### 验收标准

1. The `references/script-style.md`（新增）shall 完整描述以下规范：
   - **最高约束**：`len(script.md) / len(article.md) ≥ 0.6`（仅当 `article.md` 存在）
   - **形式 8 条原则**：口语化 / 短句 ≤ 20 字 / 第二人称 / 3 秒钩子 / `---` 节拍分隔 / 数字翻译成感受 / 不堆结构词 / 具体例子优先
   - **风骨 5 类去 AI 味**：假共情 / 假深刻 / 自我标榜 / 万能模板 / 排比堆砌
   - **念出来测试**：随机挑 3 段念出声，念到说不出口的标记为 AI 味
2. The `agents/scriptwriter.md` shall 强制 Scriptwriter 在写完 `script.md` 后跑三层自检（形式 / 风骨 / 念出来），并在 self-check 报告中输出每条结果。
3. When `article.md` 存在 and `len(script.md) / len(article.md) < 0.6`, the script ratify shall 失败并要求 Scriptwriter 重写（不允许压缩到 30% 然后假装完成）。
4. The script ratify shall 检测高频 AI 指纹词汇（"说白了 / 本质上 / 底层逻辑 / 恰恰 / 反而 / 正是因为 / 归根结底 / 在某种程度上"）出现频次，单稿超过 3 处 shall 报 fail。
5. The script ratify shall 检测连续 ≥ 3 句结构相同的排比，命中 shall 报 fail。
6. When 用户原始文章过长（≥ 5000 字 但目标视频 ≤ 3 分钟）, the Scriptwriter shall **明确告诉用户**"原文 X 字，按 60% 留存最少需要 Y 分钟视频，要么拉长视频要么拆成多集"，不得自作主张缩到 30%。
7. The Reviewer 脚本清单 shall 包含 `script.no_ai_taste`、`script.information_retention`、`script.read_aloud_test` 三项独立核查。

---

### 需求 3 - outline.md（人类可编辑 + 信息池 + 不写动画）

**用户故事：** 作为视频制作者，我希望 outline.md 作为开发计划与跨阶段持续记忆，规划**节奏 + 内容 + 信息密度**而**不规划动画**，且必须是人类可直接编辑的 markdown，使 Remotion Builder 在实现时仍有创作空间。

#### 验收标准

1. The `outline.md` shall 是纯 markdown（不嵌 YAML 块、不嵌 JSON），格式人类可读、可直接编辑，符合 `references/outline-format.md`（新增）的 spec。
2. The `outline.md` shall 包含且仅包含：顶部 metadata block（主题 id、总时长、章节数）+ 各章节 section（章节标题、信息池、step 列表、口播节选）+ 末尾素材清单。
3. The `outline.md` shall **禁止**包含：具体动画类型（blur/clear/wipe/弹簧）、CSS/Remotion 实现手段（filter/SVG/clip-path/`interpolate`）、动画时长数值（ms/秒）、错峰量、keyframe 数值。
4. Each step in `outline.md` shall 占 1 行，格式 `- step N (~Ts) — <屏幕内容一句话>`，仅写"舞台上有什么"不写"怎么动"。
5. Each chapter in `outline.md` shall 包含「信息池」block，从 `article.md` 抽 ≥ 3 条细节项，每条标注来源（`—— 来源 article §X / Lxx`）。
6. When `article.md` 不存在, the 信息池 shall 退化为"画面装饰元素池"，列章节装饰用的数字/对比/元数据，确保画面比口播信息密。
7. The `outline.md` 章节命名 shall 遵循：章节 id 小写连字符（`coldopen` / `why-good`）、不允许下划线/驼峰/中文。
8. The Producer shall 在 Phase 1.2 中**一次性**产出 `script.md` 与 `outline.md`（同一次思考），不拆为两个 checkpoint。
9. While `outline.md` 已存在, when Remotion Builder 开始构建, the Builder shall 强制读取 `outline.md` 作为章节边界 + 信息池来源。
10. When 用户在 Checkpoint Plan 阶段直接编辑 `outline.md`, the Producer shall 重新解析章节列表，更新 `state.yaml` 中的章节计数，不重新生成 outline。
11. The outline ratify shall 检查：每 step 单行无动画/手段；所有 step `(~Ts)` 累加 ≈ 顶部声明总时长（误差 < 10%）；每章信息池 ≥ 3 条且每条带来源标注；每章 3-8 步符合经验法则。

---

### 需求 4 - 章节列表显式契约

**用户故事：** 作为 Producer，我希望 `script-contract.json` 显式包含 chapters 字段，使下游代理对章节边界与命名规则有明确契约依据。

#### 验收标准

1. The `script-contract.json` v2.1 shall 在顶层增加 `chapters` 字段：`{ min_count, max_count, expected_titles?: string[], naming_rule: "lowercase-hyphenated" }`。
2. While `chapters` 字段不存在（v2.0 旧 contract）, the Producer shall 走兼容层从 `target_scene_count` 推导默认 chapter 数（每 4-6 step 一章）并记录 `compat_mode: v2.0`。
3. When 进入 v2.1 流程, the Producer shall 在 Setup 阶段写入默认 `chapters.min_count: 2, max_count: 4`。
4. When Scriptwriter 输出的章节数（按 `outline.md` 计数）超出 chapters.min_count/max_count, the script ratify shall 失败。
5. When 章节 id 不符合 `naming_rule`, the outline ratify shall 失败。
6. The contract version 字段 shall 从 `2`（int）升至 `"2.1"`（str）以便兼容层识别。

---

### 需求 5 - Checkpoint Plan（5 件事一次对齐）

**用户故事：** 作为视频制作者，我希望在 Phase 1 内容写完后只停一次，让我同时确认 5 件事——稿子 / outline / 主题 / 素材 / 开发模式——使 Phase 2 开始前所有关键决策已对齐。

#### 验收标准

1. When `script.md` 与 `outline.md` 都通过 ratify, the Producer shall 进入 Checkpoint Plan，向用户展示**单一**审核界面。
2. The Checkpoint Plan 输出 shall 包含 5 个对齐项：
   - **(1) 稿子**：`script.md` 字数 + 估时 + "要不要改"
   - **(2) 开发计划**：章节速览（id / 标题 / 步数 / 估时）+ "outline 要不要改"
   - **(3) 主题选择**：Producer 主动从内置主题中推荐 2-3 套（基于 `theme.json.bestFor` 匹配脚本类型/语气），列出剩余主题简介
   - **(4) 素材准备**：粗看本视频要的图清单 + 三选项 a/b/c（路径挑选 / 用户提供 / 全 placeholder）
   - **(5) 开发模式**：A 逐章确认（默认）/ B 顺序 / C 并行（subagent）
3. When 用户回复"主题你帮我选", the Producer shall 取推荐第 1 个，**告诉用户选了什么 + 为什么**，给反悔机会。
4. While 用户未明确选定主题, the Producer shall 拒绝进入 Phase 2。
5. When 用户在此节点直接编辑 `script.md` 或 `outline.md`, the Producer shall 接受编辑并跳过对应的"改不改"询问。
6. The Producer shall 在 Checkpoint Plan 之前**禁止**进入 Phase 2 任何子步骤（脚手架、Theme 应用、章节实现）。
7. The Checkpoint Plan 状态 shall 记录在 `state.yaml.milestones.script.checkpoint_plan`，状态机：`pending → presented → confirmed`。
8. When 用户回复"继续 + <模式>", the Producer shall 转写为 5 字段（script_ok=true, outline_ok=true, theme=<id>, asset_strategy=<a/b/c>, dev_mode=<A/B/C>）写入 `goal.yaml`。

---

### 需求 6 - 主题系统

**用户故事：** 作为视频制作者，我希望项目内置一套主题系统，每个主题包含独立的视觉性格（颜色、字体、hero 数字风格、分割线、卡片、装饰、节奏气质），且 Remotion Builder 必须通过 token + primitive 组件消费主题，使"换主题不破"成为硬承诺。

#### 验收标准

1. The skill shall 在 `skills/video-maker-v2/themes/` 下提供至少 5 套内置主题，每套含：
   - `theme.json` —— 元数据（`id`, `nameZh`, `nameEn`, `descriptionZh`, `mood`, `bestFor`, `palette` 名称）
   - `theme.ts` —— Remotion 项目可直接 import 的 token 对象（颜色阶梯、字体家族、padding、圆角、shadow、装饰层、动效基线）
2. 内置主题至少覆盖以下类型（参考 web-video-presentation）：
   - 1 套电影感深色（如 `midnight-press`：暖 espresso + 火热橙 + 编辑级斜体衬线）
   - 1 套报刊浅色（如 `newsroom`：报纸奶油 + 墨黑衬线 + 旗红 + 0 圆角）
   - 1 套现代主义（如 `bauhaus-bold`：米白 + 墨黑 + 原色蓝 + 0 圆角 + 4px 厚边）
   - 1 套终端复古（如 `terminal-green`：纯黑 + 磷光绿 + JetBrains Mono + CRT 扫描线）
   - 1 套精炼印刷（如 `monochrome-print`：米白 + 墨黑衬线 + 1px 发丝线 + 极静节奏）
3. Each theme.json shall 包含 `bestFor: string[]`（如 `["技术讲解", "测评对比", "深色冷峻"]`），用于 Checkpoint Plan 推荐。
4. The Remotion 项目模板 shall 提供以下 primitive 组件（在 `src/primitives/`）：
   - `<HeroNum>` —— 大数字，主题决定衬线/等宽/粗黑
   - `<Rule>` —— 分割线，主题决定 1px/4px × 实/虚
   - `<Card>` —— 卡片，主题决定圆角 + 阴影性格
   - `<StageFrame>` —— 舞台底色 + 圆角 + 装饰层 + vignette
   - `<MaskReveal>` —— 遮罩揭示动画原语
5. The `agents/remotion-builder.md` shall 强制以下 token 消费规则：
   - **必须用 token**：颜色（`theme.shell` / `surface` / `text` / `accent` 等）、字体家族（`theme.fontDisplay` / `fontBody` / `fontMono`）
   - **禁止硬编码**：hex 颜色、rgb、字体家族名
   - **章节自由发挥**：字号、padding/margin、动画时长/缓动、边框宽度、一般圆角、字距、gap
6. When Remotion Builder 实现章节, the Builder shall 通过 primitive 组件（不是手动 `style={{ ...theme.tokens }}`）接入主题性格。
7. The Reviewer 项目清单 shall 包含：
   - `project.no_hardcoded_colors_or_fonts` —— grep 章节代码无 hex / rgb / 字体名硬编码
   - `project.theme_token_centralized` —— 颜色字体走 token 消费
   - `project.primitive_components_used` —— hero 数字、分割线、卡片用 primitive 组件
   - `project.theme_swap_safe` —— 抽样切换至另一主题，章节代码不需修改
8. The skill shall 提供 `references/themes.md` 文档说明完整 token 契约 + 创作新主题流程。

---

### 需求 7 - 三种开发模式

**用户故事：** 作为视频制作者，我希望在 Phase 2 中可以根据视频规模与代理能力选择三种开发模式（逐章 / 顺序 / 并行），使开发节奏可控且可中途切换。

#### 验收标准

1. The `goal.yaml` v2.1 shall 包含字段 `dev_mode`，可选值 `chapter_by_chapter` (A) / `sequential` (B) / `parallel` (C)，默认 `chapter_by_chapter`。
2. The Producer shall 在 Checkpoint Plan 阶段询问用户选择模式，未明确选择时默认 A。
3. **第 1 章无论哪种模式都必须主线程做完 + 用户验收**（强制 anchor）。三种模式的差异仅在第 2 章及之后。
4. **模式 A（逐章确认，默认）**：每章做完都暂停验收，OK 后继续下一章。Producer 在每章后调用 `block_for_user`。
5. **模式 B（顺序）**：第 2~N 章在主线程顺序做完后**统一**验收。Producer 不在中间暂停。
6. **模式 C（并行 subagent）**：第 2~N 章用 subagent 并行实现，最大并行数由用户控制（"一次 4 章" / "一次 2 章"）。
7. When 模式 = C, the Producer 派发 subagent 时 shall 提供以下信息：
   - 当前章节 outline 段落（含信息池）
   - `references/chapter-craft.md` 路径（**单一必读入口**）
   - 当前主题 `theme.ts` 路径 + `theme.json.descriptionZh / mood / bestFor`
   - 第 1 章代码作为"代码风格"参考（**不是**视觉抄袭对象）
   - 硬规则：独立 CSS module / className 前缀（`.cd-` / `.mg-` / ...）；不修改 `chapters.ts`；完工跑 `pnpm exec tsc --noEmit`
8. When 模式 = C, the 风格不强求章节间完全一致 —— 主题 token + primitive 组件兜底视觉统一，动画/节奏/视觉演示由 chapter agent 自由发挥。
9. The `state.yaml` shall 在每个章节 milestone 中记录 `dev_mode_used` 字段，便于回溯。
10. When 用户在任何时间点说"剩下的并行" / "剩下的逐章", the Producer shall 接受中途切换 mode，更新 `goal.yaml.dev_mode` 并对未实现章节按新模式调度。
11. The Reviewer shall 对并行模式产出的章节强化以下检查：`project.chapter_isolation_intact`、`project.theme_consistency`。

---

### 需求 8 - Chapter 1 Baseline 检查点

**用户故事：** 作为 Producer，我希望第 1 章作为"方法论 + 主题 + 题材"组合的首次落地，必须主线程实现 + 用户验收，避免在错误风格上扩展剩余章节。

#### 验收标准

1. The Remotion Builder shall 分两阶段执行：Phase 1 仅实现第 1 章（含完整 theme 应用、primitive 组件接入、字幕组件、`<Composition>` 注册），Phase 2 实现剩余章节。
2. Phase 1 的产出 shall 是**完整版本**（节奏 + 视觉 + 真素材齐全），不是"骨架版" —— 用户能直接验收。
3. When Phase 1 组件实现完成, the Builder shall 调用 `pnpm exec remotion render` 生成 `remotion-project/out/chapter-01-preview.mp4`。
4. When `chapter-01-preview.mp4` 生成成功, the Producer shall 强制停顿向用户展示验收清单：
   - 视觉气质对不对？符合所选主题预期？
   - 节奏对不对？某些步太快/太慢/信息太薄？
   - 内容驱动动画是否到位？还是有几步是无脑入场动画？
   - 双源原则：屏幕画面有没有"口播没念但 article 能挂"的细节？
   - 反 AI 味检查：紫粉渐变 / 圆角彩色边框 / 假插画 / emoji 是否有？
5. The 验收选项 shall 为：`Continue` / `Adjust` / `Stop`，行为同 v2.0 设计。
6. When `goal.yaml.chapter_baseline_review = skip`, the Producer shall 跳过此检查点（escape hatch）。
7. When `outline.md` 仅 1 章, the Producer shall 自动跳过 baseline 并记录 `baseline_skipped: single_chapter`。
8. The `goal.yaml.baseline_preview_quality` shall 为 `medium`（默认，与最终同质量）/ `low`（`--scale 0.5` 加速迭代）。
9. The `chapter-01-preview.mp4` shall 永久保留在 `remotion-project/out/`，便于后续章节对比。
10. The Reviewer 项目清单 shall 在 Phase 1 完成后跑一次（仅核查第 1 章范围），在 Phase 2 完成后再跑一次（核查全片）。

---

### 需求 9 - narrations.ts 单一真相源（Remotion 适配）

**用户故事：** 作为 Remotion 工程师，我希望每章的 `narrations.ts` 是该章 step 数 + 口播文本的**唯一来源**，同时驱动音频合成、scene 数量、字幕渲染、`durationInFrames` 推导，使 5 个层（script / outline / 章节代码 / chapters.ts / 音频文件）永远不会漂移。

#### 验收标准

1. The Remotion 项目模板 shall 在 `src/chapters/<NN>-<id>/narrations.ts` 强制每章 export 一个名为 `narrations` 的数组，元素为 `{ step: number, text: string, durationInFrames?: number }`。
2. The 章节 `<Chapter>.tsx` shall 通过 `<Sequence>` 链或等价结构让每个 narration 对应一个独占场景；不允许通过其它方式定义 step 数。
3. The 章节代码内 `if (step === N)` 出现的最大 N + 1 必须 `=== narrations.length`（等价于：章节没有"游离 step"）。
4. The audio synthesis 脚本（`scripts/extract_narrations.ts` 新增）shall 扫描所有章节的 `narrations.ts`，按 `chapters.ts` 注册顺序生成 `audio-segments.json`，每条含 `{ chapter_id, step, text, audio_path }`。
5. The `synthesize-audio.sh`（基于现有 `qwen3_tts_scene.py` 改写）shall 串行调用 TTS（默认 MiniMax CLI `mmx`，回退至 qwen3 / 用户指定），自动跳过已存在 mp3 文件（断点续合不烧重复 token）。
6. When narration text 为空字符串, the synthesizer shall 跳过该 step（不烧 TTS token），Remotion `durationInFrames` 退化到字数估时（`max(45 帧, 字数 × 7.5 帧)`，按 30fps）。
7. The `durationInFrames` 推导规则 shall：优先使用 audio-manifest.json 中实测时长 + 6 帧（200ms）缓冲；若音频缺失则使用 `narrations.ts` 中显式 `durationInFrames`；若都无则字数估时退化。
8. The Reviewer 项目清单 shall 包含：
   - `project.narrations_length_matches_steps` —— `narrations.length === maxStepN + 1`
   - `project.narration_text_matches_script` —— 每条 narration 与 `script.md` 对应段落语义一致
   - `project.no_orphan_audio_files` —— `public/audio/<id>/` 中无对应 narration 的 mp3 报警
9. The TTS 默认顺序 shall 为：MiniMax CLI（`mmx`）→ qwen3（现有 `qwen3_tts_scene.py`）→ 用户指定（提示 + 接入用户脚本）。
10. The `references/audio-contract.md` shall 重写为以 `narrations.ts` 为中心的合成流程文档。

---

### 需求 10 - 章节物理隔离

**用户故事：** 作为 Remotion 工程师，我希望每章在文件系统层与样式层都物理隔离（独立目录、独立 className 前缀），使并行开发不互相污染，且单章修复可精准定位。

#### 验收标准

1. The Remotion 项目结构 shall 强制每章一个独立目录 `src/chapters/<NN>-<id>/`，至少包含 `<Chapter>.tsx`、`narrations.ts`、`<Chapter>.module.css`（CSS Modules）或等价 CSS 文件。
2. The 章节 className 命名规则 shall 为：CSS Modules 自动 scope，或显式前缀 `.<id-abbreviation>-` (`.cd-` for `coldopen`, `.mg-` for `migration` 等)。
3. The 章节代码 shall **禁止跨章 import**（不允许 `import from '../chapters/01-foo/...'`），仅允许 import：
   - `src/primitives/*`（主题 primitive 组件）
   - `src/theme.ts`（主题 token）
   - `src/components/*`（共享但非章节专属组件，如 `<SubtitleOverlay>`）
4. The 章节代码 shall **禁止修改** `chapters.ts` 之外的共享文件。
5. The `chapters.ts` 注册表 shall 是唯一允许跨章引用的文件，由 Producer 集中管理。
6. The Reviewer 项目清单 shall 包含：
   - `project.chapter_directory_isolation` —— 各章独立目录
   - `project.no_cross_chapter_imports` —— grep 无跨章 import
   - `project.css_namespace_isolation` —— CSS Modules 启用或前缀正确
   - `project.shared_files_unmodified` —— 章节实现期间未修改 `theme.ts` / primitives
7. When 模式 = C（并行）, the subagent prompt shall 在 hard rules 中显式列出本需求第 3、4 条。

---

### 需求 11 - Independent Reviewer Agent（修复后汇报铁律 + 三层降级）

**用户故事：** 作为 Producer，我希望有一个独立的 Reviewer Agent 从零核查清单，并遵循"修复后汇报"铁律——拿到 fail 结论后**先按 fail 项把产出改完**再向用户汇报——避免代理把原始失败结论甩给用户。

#### 验收标准

1. The skill shall 在 `agents/reviewer.md` 提供独立 Reviewer Agent 提示词。
2. The Reviewer Agent shall 与业务代理（Scriptwriter / Remotion Builder）**完全隔离**，不共享对话上下文，仅通过文件路径传递。
3. The Reviewer Agent shall 仅有读权限（业务工件）+ 写权限（仅 `ratify/reviewer-*.json`）。禁止编辑业务工件。
4. The skill shall 提供三份 checklist：
   - `ratify/reviewer-script-checklist.md` —— 脚本核查（信息保留、AI 味、风格、双源）
   - `ratify/reviewer-outline-checklist.md` —— outline 核查（无动画、信息池、章节切分）
   - `ratify/reviewer-project-checklist.md` —— Remotion 项目核查（theme token、primitive 组件、章节隔离、narrations 一致性）
5. The Reviewer 触发模式 shall 由 `goal.yaml.reviewer_mode` 控制：`always`（默认）/ `on_repair` / `off`。
6. The Reviewer 三层降级执行 shall 为（在 `agents/reviewer.md` 中明示）：
   - **优先 1**：Agent Teams（独立 reviewer agent，最佳隔离）
   - **优先 2**：subAgent（Task spawn，次佳）
   - **兜底**：当前 agent 自检（严格逐项，不允许"目测"）
7. **铁律（修复后汇报）**：当 Reviewer 输出 `overall_status: fail` 时，the Producer shall：
   1. 解析失败条目 + suggested_fix
   2. **自动派发对应业务代理修复**（脚本 fail → Scriptwriter；outline fail → Producer 自己；项目 fail → Remotion Builder）
   3. 修复完后**重新跑 Reviewer**（run_number+1）
   4. 仅当**修复后仍 fail** 或 **重试 ≥ 2 次**时才向用户汇报"做了 X 修复 + 仍未通过的 Y 条 + 用户决定（接受 / 继续修 / 停止）"
   5. **禁止**直接把原始 fail 结论甩给用户
8. The `state.yaml` shall 记录 Reviewer 自动修复轨迹：`reviewer_repair_log: [{ run, fail_items, dispatched_agent, repaired_items, final_status }]`。
9. When Reviewer 执行异常（超时 / tool error）, the Producer shall 视为 warn 不阻断，记录 `reviewer_unavailable: <reason>`。
10. The Reviewer Agent shall 输出结构化 JSON 报告（`ratify/reviewer-{checklist}-run-{N}.json`），含字段 `checklist_id`、`run_number`、`overall_status`、`items[].{id, category, status, evidence, suggested_fix}`。
11. The Reviewer 在跑项目清单时 shall 实际执行 `pnpm exec tsc --noEmit`，不允许仅靠静态读代码判断 TypeScript 健康。
12. When Reviewer 给出 `warn`, the Producer shall 继续流程但在 `state.yaml` 累积 warning 摘要供最终报告。

---

### 需求 12 - goal.yaml 与 state.yaml 字段扩展

**用户故事：** 作为用户，我希望通过 `goal.yaml` 控制新功能的开关与选择，并通过 `state.yaml` 观察新流程的执行状态。

#### 验收标准

1. The `goal.yaml` v2.1 shall 新增以下字段：
   - `theme: string`（必填，由 Checkpoint Plan 写入；如 `midnight-press`）
   - `dev_mode: chapter_by_chapter | sequential | parallel`（默认 `chapter_by_chapter`）
   - `parallel_max_concurrency: number`（仅 dev_mode=parallel 时有效，默认 4）
   - `chapter_baseline_review: enabled | skip`（默认 `enabled`）
   - `baseline_preview_quality: medium | low`（默认 `medium`）
   - `reviewer_mode: always | on_repair | off`（默认 `always`）
   - `dual_source_mode: enabled | script_only`（基于 article.md 是否存在自动初始化）
   - `asset_strategy: pick_existing | user_provides | placeholders`（来自 Checkpoint Plan）
   - `tts_provider: mmx | qwen3 | custom`（默认 `mmx`，未安装时降级）
2. The `state.yaml` v2.1 shall 新增：
   - `compat_mode: v2.0 | null`
   - `applied_defaults: string[]`
   - `dual_source_mode: enabled | script_only`
   - `milestones[].baseline_review: not_required | pending | approved | paused`
   - `milestones[].dev_mode_used: A | B | C`
   - `reviewer_runs[]`
   - `reviewer_repair_log[]`
   - `chapters[].{id, status, build_run, last_subagent_id}`（多章节追踪）
3. While 上述字段缺失, when Producer 加载, the Producer shall 应用默认值并在 `state.yaml.applied_defaults` 记录字段名列表。
4. When `state.yaml` 已存在且不含新字段, the Producer shall 在续跑时自动补全字段并保留旧值。

---

### 需求 13 - 向后兼容（v2.0 输出目录续跑）

**用户故事：** 作为现有 v2.0 输出目录的持有者，我希望升级到 v2.1 后仍能续跑或检查旧的 `output/<timestamp>-video-*` 目录，不会因为缺少新字段而崩溃。

#### 验收标准

1. When 加载 v2.0 旧输出目录（缺少 `outline.md`、缺少 `chapters` 字段、缺少 `theme`、缺少 `dev_mode` 等）, the Producer shall 进入兼容模式：
   - 从 `title_card` 推导 chapters
   - 不强制要求 `outline.md` 立即存在（在续跑下一阶段前再补全）
   - 默认 `theme` 为 `midnight-press`（与文档默认一致）
   - 默认 `dev_mode = chapter_by_chapter`
   - 默认 `reviewer_mode = always`
   - 在 `state.yaml.compat_mode = "v2.0"` 标记
2. The `skills/video-maker-v2/SKILL.md` description 字段 shall 标注当前版本号 `v2.1` 与对 v2.0 输出目录的兼容承诺。
3. The 现有 ratify 脚本 shall 保持不变；新增 Reviewer 报告写入独立文件名 `reviewer-*.json`，不与旧 ratify 文件冲突。
4. When 单元测试 `pnpm test:py` 与 `uv run pytest tests/deepagents_video_maker -q` 执行, the 测试套件 shall 在升级后全部通过（含需求 0 中替换后的 `test_better_harness_infrastructure_removed`）。
5. When skills 内文档更新, the 与 v2.0 行为不一致的处 shall 显式标注 `(v2.1+)` 以便代理识别版本差异。
6. The 升级 shall 不保留 better-harness 兼容层（按需求 0 移除属于一次性 breaking change）。
7. When v2.0 输出目录被识别, the Producer shall 在交互开始时显示 warning："检测到 v2.0 输出目录（缺少 X / Y / Z），已应用默认值 + 兼容层；推荐重新跑 Setup 以获得 v2.1 完整体验。"

---

## 范围说明

**包含**：

- 移除 better-harness 基础设施
- `article.md` 持久保留 + 双源原则全流程贯彻
- SCRIPT-STYLE 强化（信息保留度 60% + 8 形式原则 + 5 类去 AI 味 + 念出来测试）
- `outline.md` 人类可编辑 markdown + 信息池 + 章节命名规则 + 不写动画
- `script-contract.json` 加 `chapters` 字段并提供兼容层
- 5-in-1 Checkpoint Plan（稿子/outline/主题/素材/模式）
- 主题系统：≥ 5 套内置主题 + `theme.json` + `theme.ts` + 4 个 primitive 组件
- 3 种开发模式（A 逐章 / B 顺序 / C 并行）
- Chapter 1 Baseline 检查点（含 `chapter-01-preview.mp4`）
- `narrations.ts` 单一真相源（驱动音频 + scene 数 + 字幕 + durationInFrames）
- 章节物理隔离（目录 + CSS namespace + 跨章 import 禁令）
- Independent Reviewer Agent（3 份清单 + 三层降级 + 修复后汇报铁律）
- TTS 默认 MiniMax CLI + 降级至 qwen3 / 用户指定
- `goal.yaml` / `state.yaml` 字段扩展
- v2.0 输出目录兼容层
- 文档新增/重写：`SKILL.md`、`workflow-contract.md`、`scriptwriter.md`、`remotion-builder.md`、`agents/reviewer.md`、`references/script-style.md`、`references/outline-format.md`、`references/chapter-craft.md`、`references/themes.md`、`references/audio-contract.md`、`references/recording.md`

**不包含**（留待后续）：

- `web-video-presentation` 的网页 + 屏幕录制路线（本次仍走 Remotion render）
- 全局 `step` 计数器 + 点击推进 + Auto 模式
- `useStepper` / `STORAGE_KEY` 等 Web 运行时机制
- 字幕组件的多语言支持扩展
- Reviewer 自动修复的"自动接受 warn 升 fail"等高阶策略

---

## 待确认问题

1. **主题数量**：内置主题 5 套是否足够？是否要 8-10 套（与参考实现一致）？
2. **TTS 默认值**：参考实现默认 `mmx`，但本项目现有 `qwen3_tts_scene.py` 已经可工作。是否反过来默认 `qwen3` + 可选 `mmx`？
3. **outline.md 是否替代 `script-contract.json`**：参考实现没有 contract 概念，全靠 `outline.md` + ratify。我们是否保留 contract（向后兼容）还是逐步把契约信息搬进 outline？
4. **primitive 组件 API**：是 React Functional Component 接 props，还是 styled-system 模式（如 `styled('h1', { variant: 'hero' })`）？
5. **三层降级里"Agent Teams"在 deepagents 里对应什么**：deepagents 没有 Teams 概念，但 LangGraph 支持 supervisor 模式。是否把"优先 1"翻译为"独立 LangGraph node"，"优先 2"翻译为"deepagents 子代理 Task spawn"？
