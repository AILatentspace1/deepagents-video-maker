# 实施计划 — Stage 1: video-maker Skill 本体

按 design.md §12 的 T0-T8 节点细化为可执行 sub-task。每个 task 含：具体动作 / acceptance / 关联需求编号 / 工时估计。

**总工时估计**：约 28-32 个工作日（5-6.5 周），与 Q4=b（5-7 周）一致。

**实施纪律**：
- 每个 T 节点结束前跑一次 `pnpm skill:validate`（T0 除外，那时还没有此命令）
- 每个 T 节点结束 commit；T2/T3 内可分 commit
- conventional commits（feat / fix / docs / chore / refactor）
- task 状态用 `[ ]` 待办、`[/]` 进行中、`[x]` 完成、`[!]` 阻塞

---

## T0 仓库清理（0.5 天）

- [ ] **T0.1** 删除 `harness/` 整个目录（5 个文件：`video-maker.toml` / `video-maker-minimal.toml` / `README.md` / `GITHUB_ISSUES.md` / `FUTURE_TASKS.md`）
  - acceptance：`ls harness/` 报 "no such directory"
  - _需求: 0.1_

- [ ] **T0.2** 删除 `scripts/run-harness.ps1`
  - acceptance：文件不存在
  - _需求: 0.2_

- [ ] **T0.3** 删除 `runs/` 整个目录（12 个 stale 子目录）
  - acceptance：`ls runs/` 报 "no such directory"
  - _需求: 0.3_

- [ ] **T0.4** 修改 `package.json`，删除 `harness:validate` 与 `harness:run` 两个 scripts
  - acceptance：`jq '.scripts | keys' package.json` 不含 `harness:*`
  - _需求: 0.4_

- [ ] **T0.5** 修改 `CLAUDE.md`（项目根级），删除整段 "## Better-Harness (scriptwriter-only)"
  - acceptance：`grep -i 'better-harness' CLAUDE.md` 无输出
  - _需求: 0.5_

- [ ] **T0.6** 替换 `tests/deepagents_video_maker/test_skill_files.py` 中的 `test_harness_and_package_scripts_do_not_reference_removed_v1_or_evals` 为新的 `test_better_harness_infrastructure_removed`，断言 `harness/` 与 `harness:*` script 均不存在
  - acceptance：`uv run pytest tests/deepagents_video_maker/test_skill_files.py -q` 通过
  - _需求: 0.6_

- [ ] **T0.7** 全仓库扫一次 `grep -ri 'better.harness\|harness/video-maker'`，清理 `README.md`、`docs/`、其他根级文档中的引用
  - acceptance：grep 仅在 `specs/video-maker-v2-harness-upgrade/*.deprecated.md`、本 spec 与 commit message 中命中
  - _需求: 0.8_

- [ ] **T0.8** `skills/video-maker-v2/SKILL.md` 与 `manifest.json` 加 `[DEPRECATED]` 前缀；`CLAUDE.md` 加段落说明
  - `SKILL.md` frontmatter description 前缀 `[DEPRECATED]`
  - `SKILL.md` 文档头加段落：替代 skill 路径 / 决策依据 / 删除时间点
  - `manifest.json.description` 加 `[DEPRECATED]` 前缀
  - `CLAUDE.md` 加 "Skills" 段落说明 video-maker 为推荐路径
  - acceptance：grep 命中所有改动
  - _需求: 17.1, 17.2, 17.3_

- [ ] **T0.9** 跑全套测试验证 T0 改动不破坏现有
  - `pnpm test:py`
  - `uv run pytest tests/deepagents_video_maker -q`
  - acceptance：两者均通过
  - _需求: 0.7_

- [ ] **T0.10** commit T0 改动
  - commit message：`chore(harness): remove better-harness infrastructure + mark video-maker-v2 deprecated`
  - body 含信号断链证据（来自 design.md §11 / requirements §0 背景段）
  - _需求: 0.9_

---

## T1 skill 骨架 + manifest 校验脚本（1.5 天）

- [ ] **T1.1** 建 `skills/video-maker/` 完整目录树（空文件 / 占位）
  - 目录：`references/EXAMPLES/{hook-chapter,list-reveal,case-tech-review}/` / `agents/` / `ratify/` / `themes/{midnight-press,newsroom,bauhaus-bold,terminal-green,monochrome-print}/` / `scripts/` / `templates/{public,src/{components,primitives,hooks,registry,styles,chapters/01-example}}/`
  - acceptance：`tree skills/video-maker/ -d -L 3` 与 design.md §1 文件树一致
  - _需求: 1.1_

- [ ] **T1.2** 写 `skills/video-maker/manifest.json`
  - 字段：`name: video-maker` / `version: 0.1.0` / `category: Web Video / Presentation` / `description` / `compat: [claude-code, cursor, codex-cli]` / `homepage`
  - acceptance：`jq` 解析无报错；字段齐全
  - _需求: 1.5_

- [ ] **T1.3** 写 `skills/video-maker/SKILL.md` 骨架
  - frontmatter：`name: video-maker` / `description`（一句话覆盖触发场景）
  - 头部加 "参考 web-video-presentation 方法论 + 自行重写"声明段
  - 4 个 Phase 章节（Phase 1 内容 / Phase 2 网页开发 / Phase 3 音频 / Phase 4 录屏）骨架，每个先放 TODO 标记
  - 3 个 Checkpoint（Plan / Ch1 Baseline / Audio）骨架
  - "各阶段文件读取指南"表格（占位，T2 完成后填具体 references）
  - acceptance：`grep '^name: video-maker' SKILL.md` 命中；4 Phase 标题齐全
  - _需求: 1.2, 1.3, 1.4, 1.6, 1.7_

- [ ] **T1.4** 写 `skills/video-maker/README.md`（英文）+ `README.zh-CN.md`（中文）
  - 简介 + 安装步骤 + 触发命令 + 链接到 SKILL.md
  - acceptance：两份 README 各 ≥ 200 字
  - _需求: 1.1_

- [ ] **T1.5** 实现 `skills/video-maker/scripts/validate-skill.sh`
  - 按 design.md §8 的 14 项校验逻辑
  - 用纯 bash + jq + 标准 Unix 工具
  - 失败时退出码 1 + 逐条列出
  - 成功时 `✓ skill validation passed (M files / N themes / K references)`
  - 加 `chmod +x`
  - acceptance：当前骨架下跑会**失败**（有些占位文件没内容），但失败信息可读
  - _需求: 18.1, 18.2, 18.3, 18.4, 18.5, 18.6, 18.7, 18.8, 18.9, 18.10, 18.11_

- [ ] **T1.6** 项目根 `package.json` 加 `skill:validate` script
  - `"skill:validate": "bash skills/video-maker/scripts/validate-skill.sh"`
  - acceptance：`pnpm skill:validate` 能调用
  - _需求: 18.12_

- [ ] **T1.7** 让 `validate-skill.sh` 当前能 pass：
  - 把 6 份 references 文件先创建为占位（每份 ≥ 100 字的 "TODO: 待 T2 完成" 说明）
  - 5 套 themes 占位（每套 `theme.json` 含基本字段 + `tokens.css` 至少 100 字 placeholder）
  - 3 份 ratify checklist 占位
  - `agents/reviewer.md` 占位（≥ 50 字）
  - templates 必需文件占位（package.json / vite.config.ts 等可写最小可解析内容）
  - 4 个 scripts 占位（scaffold.sh / extract-narrations.ts / synthesize-audio.sh / record-with-playwright.ts 写最小 stub）
  - acceptance：`pnpm skill:validate` 成功输出 `✓ skill validation passed`
  - _需求: 18.10_

- [ ] **T1.8** commit T1 改动
  - commit：`feat(skill): scaffold video-maker skill skeleton + validation script`
  - _需求: 1, 18_

---

## T2 6 份 references（6-8 天）

每份 reference 写完跑一次 `pnpm skill:validate`，commit 一次。

- [ ] **T2.1** 写 `references/SCRIPT-STYLE.md`（1 天）
  - 最高约束（信息保留 ≥ 60% 含原始数字保留例外）
  - 形式 8 条原则（每条带"原文 → 改写"对比）
  - 风骨 5 类去 AI 味（每类典型禁止句式 + 改法）
  - 念出来测试
  - 自检流程（形式 → 风骨 → 念出来三层）
  - 文章过长时的"明确告诉用户"模板
  - 平台风格变体表（B 站 / 抖音 / YouTube long-form / 知乎 / 小红书）
  - acceptance：≥ 3000 字；`pnpm skill:validate` 通过
  - _需求: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

- [ ] **T2.2** 写 `references/OUTLINE-FORMAT.md`（1 天）
  - 顶部红框警告（不写动画）
  - 抽象格式示例 + 字段约定
  - 顶部 metadata block（主题 / 总时长 / 章节数）
  - 章节标题命名规则（小写连字符 / 不允许下划线/驼峰/中文）
  - 信息池条目格式（带来源标注）+ article 不存在时的退化路径
  - Step 列表（每步 1 行 / `(~Ts)` 必填 / 不写动画/手段）
  - 章节切分经验法则（每章 3-8 步 / 30-60s）
  - 末尾素材清单格式
  - 自检清单
  - 3 类章节结构示例链接到 EXAMPLES/
  - acceptance：≥ 2000 字；`pnpm skill:validate` 通过
  - _需求: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 3.11_

- [ ] **T2.3** 写 `references/CHAPTER-CRAFT.md`（2 天，最大单文档）
  - Part 0：十条原则（每条一行清单 + 一段展开解释）
  - Part 1：开工 5 问（这章讲什么 / 几步 / 信息池里挂什么 / 内在动作 / 反 AI 味）
  - Part 2：关系→动作决策树（对照 / 递进 / 列举 / 强调 → 对应视觉手段）
  - Part 3：视觉工具箱（CSS keyframes / SVG / Canvas / JS 推进 / 数据演示模式）
  - Part 4：时长参考（mood 对应基线 / 字数 ÷ 4 估时）
  - Part 5：反 AI 味反模式（紫粉渐变 / 圆角彩色边框 / emoji / 假数据 / 整章一种入场动画 / 持续闪烁）
  - Part 6：代码硬规则（必须用 token / `narrations.ts` 长度对齐 / 章节物理隔离 / 不跨章 import / `tsc --noEmit`）
  - Part 7：完工自检（12 项清单含硬性自检协议三层降级）
  - Part 8：反馈速查（4 类反馈 → 最小切片修复路径）
  - acceptance：≥ 5000 字；8 个 Part 齐全；`pnpm skill:validate` 通过
  - _需求: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8_

- [ ] **T2.4** 写 `references/THEMES.md`（1 天）
  - 主题系统总览
  - token 契约（25-35 个变量分类列表）
  - 章节对 token 的两层消费（必须用 / 自由发挥）
  - 4 个 primitive class（`.hero-num` / `.rule` / `.card` / `.stage-frame`）
  - 5 套内置主题速览表（DNA + bestFor + 适合场景）
  - 创作新主题流程（复制 → 改 token → dev 验证 → 加 bestFor）
  - mood → 时长建议参考表（非强制）
  - acceptance：≥ 2000 字；`pnpm skill:validate` 通过
  - _需求: 5.1, 5.6, 5.7, 5.8_

- [ ] **T2.5** 写 `references/AUDIO.md`（0.5 天）
  - narrations.ts 真相源段
  - audio-segments.json schema
  - mmx 默认流程（鉴权检查 / 调用脚本 / 校验时长）
  - qwen3 降级路径
  - 用户自带 TTS 最小契约
  - 故障排查表（mmx 未登录 / 401 / 中文音色 / 单段过长 / 音频 404）
  - acceptance：≥ 1500 字；`pnpm skill:validate` 通过
  - _需求: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8_

- [ ] **T2.6** 写 `references/RECORDING.md`（0.5 天）
  - 两条路径决策矩阵
  - Playwright 自动录屏完整步骤（含字体预热）
  - Playwright 失败模式与缓解方案
  - OS 录屏路径（mac / Windows / Linux 工具与设置）
  - 完成信号约定（`data-presentation-finished`）
  - acceptance：≥ 1500 字；`pnpm skill:validate` 通过
  - _需求: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8_

- [ ] **T2.7** 写 3 个 `references/EXAMPLES/` 章节结构示例（1 天）
  - `hook-chapter/`：钩子型开场（README + chapter.tsx + chapter.css 约 200 行）
  - `list-reveal/`：列举型逐个揭示
  - `case-tech-review/`：案例对比型（含 outline-snippet.md）
  - 每个示例标注 "**不是抄袭模板，是结构示意**"
  - acceptance：3 个目录齐全；每个 README ≥ 300 字
  - _需求: 4.7（间接，通过 EXAMPLES 链接）_

- [ ] **T2.8** commit T2 改动（按 reference 分 commit 或 1 个大 commit）
  - 推荐分 7 个 commit（每份 reference 一个）便于回溯
  - _需求: 2, 3, 4, 5.1/5.6-5.8, 6, 7_

---

## T3 5 套主题资产（5-6 天）

每套主题 1 天：写 `theme.json` + `tokens.css` + 用示例章节验证。

- [ ] **T3.1** `themes/midnight-press/`
  - DNA 锚点：暖色 espresso 深色 + Instrument Serif 斜体英文 + Noto Serif SC 中文 + 电影感慢节奏 + vignette 无颗粒
  - `theme.json`：`id, nameZh, descriptionZh, bestFor: ["技术深度","产品发布","故事讲述"], mood: cinematic-slow, palette: dark`
  - `tokens.css`：约 30 个变量（按 design.md §2 表格）
  - 用 `01-example` 验证视觉效果
  - acceptance：示例章节用此主题渲染合格；`pnpm skill:validate` 通过
  - _需求: 5.2, 5.3, 5.4, 5.5_

- [ ] **T3.2** `themes/newsroom/`
  - DNA 锚点：NYT 报刊 + 纸黄底 + 墨黑衬线 + 旗红 + Playfair Display + 0 圆角
  - acceptance：同上
  - _需求: 5.2, 5.3, 5.4, 5.5_

- [ ] **T3.3** `themes/bauhaus-bold/`
  - DNA 锚点：现代主义 + 米白 + 墨黑 + 原色蓝 + Archivo Black + 0 圆角 + 4px 实色厚边 + 偏移实色阴影
  - acceptance：同上
  - _需求: 5.2, 5.3, 5.4, 5.5_

- [ ] **T3.4** `themes/terminal-green/`
  - DNA 锚点：80s 磷光终端 + 纯黑 + JetBrains Mono only + CRT 扫描线 + 磷光 text-shadow
  - 注意 CRT 扫描线用 `repeating-linear-gradient`
  - acceptance：同上
  - _需求: 5.2, 5.3, 5.4, 5.5_

- [ ] **T3.5** `themes/monochrome-print/`
  - DNA 锚点：安静印刷杂志 + 米白 + 墨黑衬线 + 墨蓝 accent + Source Serif + 1px 实线 + 无装饰
  - acceptance：同上
  - _需求: 5.2, 5.3, 5.4, 5.5_

- [ ] **T3.6** 跨主题验证：用同一个 `01-example` 章节代码切换 5 套主题，截图对比，确保章节代码无硬编码颜色/字体
  - 实施方式：每套主题 `cp themes/<id>/tokens.css templates/src/styles/tokens.css` 后跑 dev server，截图
  - acceptance：5 套主题视觉差异明显但章节代码 0 修改
  - _需求: 5.7（章节代码不得硬编码）_

- [ ] **T3.7** commit T3
  - commit：`feat(skill): add 5 built-in themes (midnight-press / newsroom / bauhaus-bold / terminal-green / monochrome-print)`
  - _需求: 5_

---

## T4 Reviewer + 3 份 ratify checklist（2 天）

- [ ] **T4.1** 写 `agents/reviewer.md`（独立 Reviewer agent 提示词）
  - 角色定义 + 三层降级（Tier 1 Agent Teams / Tier 2 subAgent / Tier 3 自检）
  - 输入变量约定
  - 工作流（读清单 / 逐项核查 / 写报告 / 报告自身执行结果）
  - 硬性约束（仅读权限 + 写报告权限 / 禁修改业务工件 / 不允许"凭印象"通过 / 不确定标 warn）
  - 报告 JSON schema（按 design.md §6.5）
  - 修复后汇报铁律段
  - acceptance：≥ 800 字；含三层降级 + 铁律
  - _需求: 14.1, 14.2, 14.3_

- [ ] **T4.2** 写 `ratify/reviewer-script-checklist.md`
  - 信息保留度 ≥ 60%（仅当 article.md 存在）
  - 形式 8 条逐条核查
  - 风骨 5 类逐条核查
  - AI 高频词检测（"说白了 / 本质上 / 底层逻辑 / 恰恰 / 反而 / 正是因为 / 归根结底 / 在某种程度上"）
  - 排比连续 ≥ 3 句结构相同检测
  - 念出来测试条目
  - acceptance：≥ 1500 字；与 SCRIPT-STYLE.md 自检清单对齐
  - _需求: 14.6_

- [ ] **T4.3** 写 `ratify/reviewer-outline-checklist.md`
  - 每 step 单行无动画/手段
  - 所有 step `(~Ts)` 累加 ≈ 总时长（误差 < 10%）
  - 每章信息池 ≥ 3 条且每条带来源标注
  - 每章 3-8 步符合经验法则
  - 章节命名符合 lowercase-hyphenated
  - 末尾素材清单格式正确
  - acceptance：≥ 1000 字；与 OUTLINE-FORMAT.md 自检清单对齐
  - _需求: 14.6_

- [ ] **T4.4** 写 `ratify/reviewer-project-checklist.md`
  - 每章 ≥ 1-2 处 CSS/SVG/Canvas/JS 视觉演示
  - 不同 step 主导动作不一样（无整章一种动画）
  - 字号大留白舒服
  - 清单逐个揭示（1 项 = 1 step）
  - 画面信息密度 > 口播信息密度
  - 无紫粉渐变 / 圆角彩色边框 / emoji / 假数据 / 假 logo
  - 无硬编码 hex / 字体名（仅用 token）
  - hero-num/rule/card/stage-frame primitive 使用正确
  - `narrations.ts` 长度对齐章节代码
  - 每条 narration 与 script.md 对应段语义一致
  - 每 step 动画时长 ≤ 口播时长
  - 章节物理隔离（独立 CSS 前缀 / 不跨章 import）
  - 未修改 `chapters.ts` 之外的共享文件
  - `npx tsc --noEmit` 通过
  - 无小号字体大量纯文字
  - 无页眉页脚
  - acceptance：≥ 2000 字；与 CHAPTER-CRAFT.md Part 7 完工自检对齐
  - _需求: 14.6_

- [ ] **T4.5** `pnpm skill:validate` 通过
  - _需求: 18_

- [ ] **T4.6** commit T4
  - commit：`feat(skill): add reviewer agent prompt + 3 ratify checklists`
  - _需求: 14_

---

## T5 Vite + React 项目模板（5-7 天）

- [ ] **T5.1** 写 `templates/{package.json, tsconfig.json, vite.config.ts, index.html}`（0.5 天）
  - `package.json` deps：react ^18 / react-dom ^18 / vite ^5 / typescript ^5；devDeps：@types/react / @vitejs/plugin-react
  - `package.json` scripts：`dev` / `build` / `preview` / `extract-narrations` / `synthesize-audio` / `record`
  - `tsconfig.json`：strict mode / jsx: react-jsx / target: ES2022
  - `vite.config.ts`：含 `@vitejs/plugin-react` + `base: './'`（便于 build 后任意路径预览）
  - `index.html`：基础 HTML5 框架，挂 `<div id="root">`
  - acceptance：进 `templates/` 跑 `npm install && npm run dev` 起来不报错（暂时白屏 OK）
  - _需求: 8.1, 8.9_

- [ ] **T5.2** 写 `templates/src/styles/*`（0.3 天）
  - `base.css`：reset + 16:9 舞台基础（`.scene` / `.scene-pad` / `.stage-frame`）+ 4 个 primitive class 占位定义（`.hero-num` / `.rule` / `.card` / `.stage-frame`）使用 token
  - `tokens.css`：占位（`:root { --shell: #1a120c; ... }` 默认 midnight-press，被脚手架覆盖）
  - `animations.css`：共享 keyframes（`@keyframes mask-reveal` / `@keyframes fade-in` 等基础）
  - `fonts.css`：`@import` Google Fonts（每个内置主题用到的字体一并 import）
  - acceptance：CSS 解析无报错；4 套字体加载
  - _需求: 8.5_

- [ ] **T5.3** 写 `templates/src/registry/{types.ts, chapters.ts}`（0.3 天）
  - `types.ts`：`ChapterStepProps` / `ChapterDef` / `Narration = string` 等
  - `chapters.ts`：示例只注册 `01-example`，包含 `import ExampleChapter from "../chapters/01-example/Example"; import { narrations as exampleNarrations } from "../chapters/01-example/narrations";`
  - acceptance：TS 编译通过
  - _需求: 8.6_

- [ ] **T5.4** 写 `templates/src/hooks/{useStepper.ts, useAudioPlayer.ts}`（1 天）
  - `useStepper`：章节 + step 游标 / `STORAGE_KEY = "video-maker-stepper-v1"` 持久化 / `next/prev/jumpToChapter` / **挂 `data-presentation-finished` 到 body** 当 `isFinished`
  - `useAudioPlayer`：单 hidden audio 元素 / mode 切换 / `audio.ended → trailMs → onAutoAdvance` / error/missing 退化估时
  - acceptance：TS 编译通过；单元 mock 测试游标推进逻辑（可选）
  - _需求: 8.3, 8.8_

- [ ] **T5.5** 写 `templates/src/hooks/{useAutoMode.ts, useStageScale.ts}`（0.5 天）
  - `useAutoMode`：解析 URL `?auto=1` / `?audio=1` / 监听 `M` 键切换三模式
  - `useStageScale`：监听 viewport resize / 计算 `1920×1080 → viewport` 的 transform scale
  - acceptance：TS 编译通过
  - _需求: 8.3_

- [ ] **T5.6** 写 `templates/src/components/{Stage.tsx, ProgressBar.tsx, ProgressBar.css}`（0.5 天）
  - `Stage`：16:9 舞台容器 + `useStageScale` 适配 + 点击空白 → `onAdvance`
  - `ProgressBar`：默认 `opacity: 0` 隐藏，鼠标悬到底部边缘才出现 + 章节跳转逻辑
  - acceptance：dev server 中能看到 16:9 舞台居中
  - _需求: 8.2_

- [ ] **T5.7** 写 `templates/src/components/{AutoStartGate.tsx/css, AutoToggle.tsx/css, SubtitleOverlay.tsx}`（0.5 天）
  - `AutoStartGate`：Auto 模式蒙层 + `data-auto-start-gate` 属性（供 Playwright 监听）+ 按 SPACE 启动
  - `AutoToggle`：右上角 hover 出现 + 三模式切换按钮
  - `SubtitleOverlay`：屏幕底部字幕条 + 半透明衬底 + 从 `narrations.ts` 取当前 step 文本
  - acceptance：dev server 中按 SPACE 触发 Auto；M 键切换模式
  - _需求: 8.2_

- [ ] **T5.8** 写 `templates/src/components/MaskReveal.tsx`（0.3 天）
  - 接受 `show` / `delay` / `duration` props
  - CSS keyframes 实现 mask 揭示动画
  - acceptance：示例章节中可直接用
  - _需求: 8.2_

- [ ] **T5.9** 写 `templates/src/primitives/{HeroNum,Rule,Card,StageFrame}.tsx`（0.3 天）
  - 4 个 React functional component，仅渲染对应 class 的 `<span>` / `<hr>` / `<div>`
  - 通过 `...rest` 透传 HTML 属性
  - acceptance：可在示例章节中 `<HeroNum>3.4×</HeroNum>` 使用
  - _需求: 8.4_

- [ ] **T5.10** 写 `templates/src/{main.tsx, App.tsx}`（1 天）
  - `main.tsx`：React root mount + import styles
  - `App.tsx`：组装 `useStepper` + `useAutoMode` + `useAudioPlayer` + `Stage` + `ProgressBar` + `AutoToggle` + `AutoStartGate` + `SubtitleOverlay`
  - 监听 `useStepper.isFinished` 挂 `data-presentation-finished` 到 `<body>`
  - audio path 约定：`${import.meta.env.BASE_URL}audio/<id>/<step+1>.mp3`
  - acceptance：dev server 中第一章 step 0/1/2 切换正常；Auto 模式按 SPACE 整片自动跑通（无音频时退化估时）
  - _需求: 8.2, 8.8_

- [ ] **T5.11** 写 `templates/src/chapters/01-example/{Example.tsx, Example.css, narrations.ts}`（0.5 天）
  - 3 个 step 示例：cover / split-layout / pull-quote close
  - 用 token + primitive class（不硬编码颜色）
  - `narrations.ts`：3 条 string，长度 = 3
  - acceptance：dev server 中 3 个 step 切换显示正确
  - _需求: 8.7_

- [ ] **T5.12** 实测 templates 完整可跑
  - `cp -r templates /tmp/test-vite-app`
  - `cd /tmp/test-vite-app && npm install && npm run dev`
  - 浏览器打开 `http://localhost:5173`
  - 验证：3 个 step 能切换 / Auto 模式按 SPACE 跑通
  - `npm run build && npm run preview` 也跑通
  - acceptance：以上全部通过
  - _需求: 8.1_

- [ ] **T5.13** `pnpm skill:validate` 通过
  - _需求: 18_

- [ ] **T5.14** commit T5
  - commit：`feat(skill): add Vite + React project template (hooks / components / primitives / styles / example chapter)`
  - _需求: 8, 10_

---

## T6 4 个 scripts（4-5 天）

- [ ] **T6.1** 写 `scripts/scaffold.sh`（0.5 天）
  - 接收：`<output-dir>` + `--theme=<id>`（默认 midnight-press）+ `--list-themes`
  - 校验输出目录不存在或为空
  - 复制 `templates/` 到目标
  - 复制选定主题 `themes/<id>/tokens.css` → `<output-dir>/src/styles/tokens.css`
  - 写 `<output-dir>/.theme` 记录主题 id
  - 打印 next steps
  - `--list-themes` 读 `themes/*/theme.json` 按 nameZh + bestFor 列出
  - acceptance：脚手架到临时目录 + npm install + npm run dev 跑通
  - _需求: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

- [ ] **T6.2** 写 `scripts/extract-narrations.ts`（0.5 天）
  - tsx / ts-node 可执行
  - 跑在 Vite 项目内（`presentation/`）：`import { CHAPTERS } from "./src/registry/chapters"`
  - 按章节顺序生成 `audio-segments.json`
  - 空 narration 跳过（不烧 TTS token）
  - 输出格式：`[{chapter, step, text, audio}]`
  - acceptance：在测试项目内跑能产出正确 JSON
  - _需求: 10.8_

- [ ] **T6.3** 写 `scripts/synthesize-audio.sh`（1.5 天）
  - 跑在 Vite 项目内
  - `which mmx` → 走 mmx；否则检测 `qwen3_tts_scene.py` → 走 qwen3；否则提示用户三选项
  - mmx 鉴权检查（`mmx auth status`），未登录给登录命令
  - 串行调用（避免 rate limit）
  - 自动跳过已存在文件（断点续合）
  - 每条打印进度
  - 全部完成后跑 ffprobe 报告时长 + 警告 ≥ 15s 条目
  - 支持 `--force` 全部重合 / `--voice=<id>` 指定音色
  - acceptance：mmx 路径跑通（可用 echo mock）+ qwen3 降级路径跑通
  - _需求: 6.3, 6.4, 6.5, 6.6_

- [ ] **T6.4** 写 `scripts/record-with-playwright.ts`（2 天，最难单脚本）
  - 接收参数：`<presentation-dir>` + `--output=<path.mp4>` + `--viewport=1920x1080` + `--fps=30` + `--retries=2`
  - 步骤按 design.md §5.1 的 15 步
  - 自动 `npm run build && npm run preview`
  - 字体预热（`document.fonts.ready` + 200ms）
  - 等 AutoStartGate
  - `page.video()` 录制启动
  - 按 SPACE
  - 等 `data-presentation-finished="true"` + 500ms 缓冲
  - 关闭 page → 拿到 webm
  - ffmpeg 转 mp4 + 裁头部 200ms 黑屏
  - 失败重试（按 design.md §5.2 表格的 7 类失败模式）
  - 打印 `✓ Recorded: <path> | Duration: Xs | Size: YMB`
  - acceptance：在 templates 默认 example 章节上跑通；产出可播放 mp4
  - _需求: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7, 15.8, 15.9, 15.10_

- [ ] **T6.5** 实测 4 个 scripts 各自能跑（0.5 天）
  - scaffold.sh → 临时目录 → npm install + npm run dev 通
  - extract-narrations.ts → 临时项目 → audio-segments.json 正确
  - synthesize-audio.sh → 用 echo 替代 mmx 测决策树
  - record-with-playwright.ts → 临时项目 → final.mp4 可播
  - acceptance：以上全部通过
  - _需求: 9.4, 15.8_

- [ ] **T6.6** `pnpm skill:validate` 通过
  - _需求: 18_

- [ ] **T6.7** commit T6（建议分 4 个 commit，每个脚本一个）
  - _需求: 6, 9, 10.8, 15_

---

## T7 端到端 Demo（2-3 天，含视频内容质量打磨）

- [ ] **T7.1** 选 1 篇 Anthropic 博客作为 demo article
  - 浏览 https://www.anthropic.com/news 或 https://www.anthropic.com/research 选近 6 个月内 1 篇
  - 字数 1500-3000 之间（适合 2-3 分钟视频）
  - 复制原文 + 标注 source URL 到 `demos/anthropic-article-demo/article.md`
  - acceptance：article.md 存在 + commit message 标注来源
  - _需求: 16.2_

- [ ] **T7.2** 跑 Phase 1：Producer 一次产出 `script.md` + `outline.md`
  - 在 `demos/anthropic-article-demo/` 新会话调用 `/video-maker`
  - 触发 SKILL.md Phase 1.2
  - Scriptwriter 走 SCRIPT-STYLE 三层自检
  - 产出 `script.md` + `outline.md`
  - acceptance：两份文件齐全；信息保留度 ≥ 60%；outline 含信息池 ≥ 3 条/章
  - _需求: 16.3_

- [ ] **T7.3** Reviewer 跑 script + outline 两份 checklist
  - Tier 选择按当前会话能力（优先 Task spawn / Tier 2）
  - 产出 `ratify/reviewer-script-run-1.json` + `reviewer-outline-run-1.json`
  - 如有 fail → 修复后再跑（按铁律）
  - acceptance：两份 reviewer 报告 overall_status ∈ {pass, warn}
  - _需求: 16.3_

- [ ] **T7.4** Checkpoint Plan：5 件事一次对齐
  - Producer 主动展示 5 选项
  - 决策：theme=`midnight-press`（或其他选定）/ asset_strategy=全 placeholder / dev_mode=A 逐章
  - 写 `presentation/.video-maker-state.yaml`
  - acceptance：5 项决策都有显式记录
  - _需求: 16.3_

- [ ] **T7.5** Phase 2：脚手架 + 第 1 章 + Ch1 Baseline
  - 跑 `bash skills/video-maker/scripts/scaffold.sh demos/anthropic-article-demo/presentation --theme=midnight-press`
  - 删除 `01-example`
  - 实现第 1 章（主线程）
  - 跑 dev server 给"用户"（你/Reviewer）验收
  - 验收 5 项核查重点
  - 通过后继续；不通过则修改第 1 章
  - acceptance：第 1 章 dev server 跑起来视觉合格 + tsc 通过
  - _需求: 16.3_

- [ ] **T7.6** 第 2-N 章逐章实现（dev_mode=A）
  - 每章独立验收
  - 每章独立 CSS 前缀
  - 每章 narrations.ts 长度对齐
  - acceptance：所有章节实现完成 + dev server 完整可跑 + tsc 通过
  - _需求: 16.3_

- [ ] **T7.7** Reviewer 跑 project full checklist
  - 产出 `ratify/reviewer-project-run-1.json`
  - 如有 fail → 修复
  - acceptance：reviewer 报告 overall_status ∈ {pass, warn}
  - _需求: 16.3_

- [ ] **T7.8** Checkpoint Audio + Phase 3 音频合成
  - 用户决策：合成
  - 跑 `npm run extract-narrations` 产 `audio-segments.json`
  - 让用户/agent 扫一眼确认文本对
  - 跑 `npm run synthesize-audio`（mmx 或 qwen3）
  - acceptance：`public/audio/<id>/*.mp3` 各章齐全；ffprobe 时长报告无 ≥ 15s 警告
  - _需求: 16.3_

- [ ] **T7.9** Phase 4：Playwright 录屏
  - 跑 `tsx skills/video-maker/scripts/record-with-playwright.ts demos/anthropic-article-demo/presentation --output=demos/anthropic-article-demo/final.mp4`
  - 验证 final.mp4 可播放（QuickTime / VLC）
  - 验证视频时长 = sum(audio durations) ± 5%
  - acceptance：final.mp4 ≥ 60s 且可播放；视觉与 dev server 一致
  - _需求: 16.3_

- [ ] **T7.10** 写 `demos/anthropic-article-demo/RUN-LOG.md`
  - 关键节点时间戳
  - Reviewer 报 fail 的项目 + 修复轮数
  - 最终 MP4 时长 / 大小
  - 经验教训（"这套主题 + 这种内容 表现如何"）
  - acceptance：RUN-LOG.md ≥ 500 字
  - _需求: 16.4_

- [ ] **T7.11** commit demo 全部产物
  - commit：`demo: anthropic article end-to-end run with video-maker skill`
  - 含：article.md / script.md / outline.md / presentation/ / final.mp4 / RUN-LOG.md / 3 份 reviewer-*.json
  - 注意：final.mp4 可能较大（10-50MB），考虑 git LFS 或单独 release attachment
  - acceptance：仓库内 demo 目录完整；MP4 通过 git push 成功（如超 100MB 用 LFS）
  - _需求: 16.1, 16.5_

---

## T8 阶段 1 验收 + PR（0.5 天）

- [ ] **T8.1** 最终 `pnpm skill:validate` 通过
  - 全部 18 项校验
  - acceptance：`✓ skill validation passed (M files / 5 themes / 6 references)` 输出
  - _需求: 18.10_

- [ ] **T8.2** 全套测试通过
  - `pnpm test:py`
  - `uv run pytest tests/deepagents_video_maker -q`
  - acceptance：两者均通过
  - _需求: 0.7_

- [ ] **T8.3** 写 PR 描述
  - 标题：`feat(skill): video-maker skill (Stage 1 — Web 录屏路线 skill 本体)`
  - body：
    - 链接到 `specs/video-maker-web-port/stage-1-skill/` 三份 spec
    - 关键决策（路线 1 + 阶段 2 计划 + better-harness 移除）
    - demo 视频链接
    - 测试结果
    - 阶段 2 路线图简介
    - 不破坏什么 / 破坏什么（v2 标 deprecated 但未删）
  - acceptance：PR description 含上述全部段落
  - _需求: 16.6（结项验收标志）_

- [ ] **T8.4** 提 PR
  - `gh pr create --title "..." --body "..."`
  - acceptance：PR URL 拿到 + CI 通过（如有）
  - _需求: 全部_

---

## 验收清单（Stage 1 完成 = 以下全部 [x]）

- [ ] T0-T8 全部 task 完成
- [ ] `skills/video-maker/` 目录结构与 design.md §1 完全一致
- [ ] `pnpm skill:validate` 输出 `✓ skill validation passed`
- [ ] `pnpm test:py` 与 `uv run pytest tests/deepagents_video_maker -q` 全部通过
- [ ] `demos/anthropic-article-demo/final.mp4` 存在且可播放
- [ ] `demos/anthropic-article-demo/RUN-LOG.md` 存在且 ≥ 500 字
- [ ] 3 份 reviewer-*-run-*.json 报告齐全且 status ∈ {pass, warn}
- [ ] `skills/video-maker-v2/` 标 `[DEPRECATED]` 但未删除
- [ ] `harness/` 与 `runs/` 已删除
- [ ] PR 已提且通过 CI

---

## 阶段 2 入口预告

阶段 1 完成后，阶段 2 spec（`specs/video-maker-web-port/stage-2-deepagents/`）从以下问题开始：

- video-maker skill 阶段 1 的产物结构如何映射到 `vm_*` LangChain tools？
- 现有 `src/deepagents_video_maker/` 哪些文件保留 / 重写 / 删除？
- `tests/deepagents_video_maker/` 全套测试如何重组？
- `skills/video-maker-v2/` 的实际删除时机？
- `.deepagents/skills/` 目录是否需要新增 video-maker 子代理 wrapper？

阶段 2 spec 在阶段 1 PR merge 后再开始写。
