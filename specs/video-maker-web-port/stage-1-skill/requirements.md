# 需求文档 — Stage 1: video-maker Skill 本体（Web 录屏路线）

## 介绍

本 spec 是 video-maker-web-port 的**阶段 1**：构建一个独立可跑的 `skills/video-maker/` skill，输出"伪装成网页的视频"——Vite + React + TypeScript 项目，配合 Playwright 自动录屏产出 MP4。**阶段 1 完全不依赖 DeepAgents Python 工具链**，任何 Claude Code / Cursor / Codex 用户安装该 skill 即可使用。

**方法论参考但不直接 fork**：方法论参考 [`ConardLi/garden-skills/skills/web-video-presentation`](https://github.com/ConardLi/garden-skills/tree/main/skills/web-video-presentation) 的成熟实践，但所有 skill 文件、references、模板、主题、脚本由本项目**自行重写**，不直接拷贝原文（避免 attribution 与未来方法论分叉问题）。

**核心方法论**（来自 web-video-presentation 提炼，本 skill 保留并精炼）：

1. **双源原则**：`script.md` 决定节拍 + `article.md` 决定画面信息密度
2. **信息池**：outline 每章首段从 article 抽细节，让画面信息密度 > 口播
3. **5-in-1 Checkpoint**：稿子 + outline + 主题 + 素材 + 开发模式一次对齐
4. **3 种开发模式**：A 逐章 / B 顺序 / C 并行（subagent）
5. **Chapter 1 Baseline**：第 1 章主线程 + 强制人审，作为后续章节风格锚
6. **SCRIPT-STYLE**：信息保留度 ≥ 60% + 8 形式原则 + 5 类去 AI 味 + 念出来测试
7. **CHAPTER-CRAFT**：10 原则 + 决策树 + 反 AI 味反模式 + 完工自检
8. **主题系统**：5 套主题，token + primitive class，章节代码主题无关
9. **`narrations.ts` 单一真相源**：每章 `narrations.ts` 同时驱动 step 数 + 字幕 + 音频合成
10. **三层降级 Reviewer**：Agent Teams → subAgent → 当前 agent 自检；铁律是"修复后再汇报"
11. **Auto 模式 + Playwright 自动录屏**：替代/补充 OS 屏幕录制，可 CI 化

**与现有 `skills/video-maker-v2/`（Remotion 路线）的关系**：

| 维度 | 处理 |
|---|---|
| 目录命名 | 新 skill 命名 `skills/video-maker/`（与 v2 并存一段时间） |
| 旧 skill 状态 | `skills/video-maker-v2/` 标记 deprecated，阶段 2 完成后删除 |
| 现有 Python 工具 | 阶段 1 不动；阶段 2 才适配 |
| 现有 Remotion 资产 | 阶段 1 不动；阶段 2 一并清理 |
| `specs/video-maker-v2-harness-upgrade/` | 已加 `.deprecated.md` 后缀，归档不删除 |

**升级范围**（阶段 1）：

| 分组 | 需求编号 | 内容 |
|---|---|---|
| 仓库清理 | 0 | 移除 better-harness 基础设施 |
| Skill 骨架 | 1 | 新建 `skills/video-maker/` 目录与 SKILL.md |
| 方法论文档 | 2, 3, 4, 5, 6 | SCRIPT-STYLE / OUTLINE-FORMAT / CHAPTER-CRAFT / THEMES / AUDIO / RECORDING references |
| 主题资产 | 7 | 5 套主题（theme.json + tokens.css） |
| 模板与脚手架 | 8, 9 | Vite + React 项目模板 + `scaffold.sh` |
| 单源真相机制 | 10 | `narrations.ts` 契约与运行时消费 |
| 主流程节点 | 11, 12, 13 | 5-in-1 Checkpoint + 3 种开发模式 + Ch1 Baseline |
| 独立审查 | 14 | Reviewer agent + 三层降级 + 修复后汇报 |
| 录屏自动化 | 15 | Playwright 自动录屏 |
| 端到端验证 | 16 | Anthropic 博客文章端到端 demo |
| 旧 skill 状态 | 17 | `skills/video-maker-v2/` 标记 deprecated |
| skill 自检 | 18 | manifest 校验脚本（确保 skill 自身完整性） |

## 需求

### 需求 0 - 移除 better-harness 基础设施

**用户故事：** 作为维护者，我希望移除已无实际优化信号的 better-harness 基础设施，避免它持续占用文档篇幅、误导代理认为该路径仍可用。

**背景信号断链证据：**

- `harness/video-maker-minimal.toml` 唯一可优化 surface 是 `skills/video-maker-v2/agents/scriptwriter.md`
- 但 7 个 `[[cases]]` 引用的测试均为合成输入的 ratify 单元测试或文件存在性测试，不调用 LLM、不读取 `scriptwriter.md`
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

---

### 需求 1 - skill 骨架与 SKILL.md

**用户故事：** 作为视频制作者，我希望在 `skills/video-maker/` 下找到一个完整自洽的 skill，安装到 `~/.claude/skills/` 后能在任意工作目录通过 `/video-maker` 触发完整流程。

#### 验收标准

1. The `skills/video-maker/` 目录 shall 包含：`SKILL.md`、`manifest.json`、`README.md`、`README.zh-CN.md`、`references/`、`themes/`、`scripts/`、`templates/`。
2. The `SKILL.md` shall 在 frontmatter 中包含 `name: video-maker` 与一句话 description，使代理在用户输入"做视频/口播稿/web 视频"时能命中此 skill。
3. The `SKILL.md` shall 完整描述 4 个 Phase + 3 个硬节点 Checkpoint（Plan / Ch1 Baseline / Audio）的工作流。
4. The `SKILL.md` shall 提供"各阶段文件读取指南"表格，说明每个 phase 必读哪些 references，避免长会话中代理一次读全。
5. The `manifest.json` shall 包含 `name: video-maker`、`version`、`category`、`description`、`compat: [claude-code, cursor, codex-cli]`。
6. The `SKILL.md` shall 在头部标注"参考 web-video-presentation 方法论 + 自行重写"声明，不直接复制原文。
7. The 整个 skill 内容 shall 不引用 `skills/video-maker-v2/` 或任何 Remotion 工件路径，保证可独立分发。

---

### 需求 2 - SCRIPT-STYLE.md：信息保留 + 形式 + 风骨

**用户故事：** 作为内容质量负责人，我希望 Scriptwriter 在写口播稿时遵循信息保留度 ≥ 60% + 8 形式原则 + 5 类去 AI 味 + 念出来测试的硬性规范。

#### 验收标准

1. The `references/SCRIPT-STYLE.md` shall 描述**最高约束**：`len(script.md) / len(article.md) ≥ 0.6`（仅当 article.md 存在）；关键事实/数字/案例/论证链不得整段消失。
2. The `references/SCRIPT-STYLE.md` shall 列出**形式 8 条原则**：口语化 / 短句 ≤ 20 字 / 第二人称 / 3 秒钩子 / `---` 节拍分隔 / 数字翻译成感受 / 不堆结构词 / 具体例子优先；每条提供"原文 → 改写"的对比示例。
3. The `references/SCRIPT-STYLE.md` shall 列出**风骨 5 类去 AI 味**：假共情 / 假深刻 / 自我标榜 / 万能模板 / 排比堆砌；每类列出典型禁止句式 + 改法。
4. The `references/SCRIPT-STYLE.md` shall 包含**念出来测试**：随便挑 3 段念出声，念到说不出口/想跳过/想笑出声的标记为 AI 味。
5. The `references/SCRIPT-STYLE.md` shall 包含**自检流程**：写完 script.md 后强制走 形式自检 → 风骨自检 → 念出来测试 三层；要求三层全过才能产出 outline。
6. When `article.md` 过长（≥ 5000 字 但目标视频 ≤ 3 分钟）, the `SCRIPT-STYLE.md` shall 要求 Scriptwriter 明确告诉用户"原文 X 字，按 60% 留存最少需要 Y 分钟视频"，不得自作主张缩到 30%。
7. The `SCRIPT-STYLE.md` shall 提供平台风格变体表（B 站 / 抖音 / YouTube long-form / 知乎 / 小红书）的句长 / 钩子节奏 / 信息密度差异。

---

### 需求 3 - OUTLINE-FORMAT.md：人类可编辑 + 信息池 + 不写动画

**用户故事：** 作为视频制作者，我希望 outline.md 作为开发计划与跨阶段持续记忆，规划节奏 + 内容 + 信息密度，**不规划动画**，且必须人类可直接编辑。

#### 验收标准

1. The `references/OUTLINE-FORMAT.md` shall 在文档顶部用红框标注"outline 是开发计划，不是视觉规划；只规划节奏 + 内容 + 信息密度，不写动画"。
2. The `outline.md` 格式 shall 是纯 markdown（不嵌 YAML 块、不嵌 JSON），所有 metadata 用 markdown 引用块（`>`）形式。
3. The `outline.md` shall 包含且仅包含：顶部 metadata block（主题 id、总时长、章节数）+ 各章节 section（章节标题 + 信息池 + step 列表 + 口播节选）+ 末尾素材清单。
4. The `outline.md` shall **禁止**包含：具体动画类型（blur/clear/wipe/弹簧）、CSS/Remotion 实现手段、动画时长数值、错峰量、keyframe 数值。
5. Each step in `outline.md` shall 占 1 行，格式 `- step N (~Ts) — <屏幕内容一句话>`，仅写"舞台上有什么"不写"怎么动"。
6. Each chapter in `outline.md` shall 包含「信息池」block，从 `article.md` 抽 ≥ 3 条细节项，每条标注来源（`—— 来源 article §X / Lxx`）。
7. When `article.md` 不存在, the 信息池 shall 退化为"画面装饰元素池"，列章节装饰用的数字/对比/元数据。
8. The 章节命名 shall 遵循：章节 id 小写连字符（`coldopen` / `why-good`），不允许下划线/驼峰/中文。
9. The `OUTLINE-FORMAT.md` shall 提供 3 类章节结构示例：钩子型开场 / 列举型 / 案例对比型。
10. The `OUTLINE-FORMAT.md` shall 包含**自检清单**：每 step 单行无动画/手段；所有 step `(~Ts)` 累加 ≈ 总时长（误差 < 10%）；每章信息池 ≥ 3 条且每条带来源；每章 3-8 步符合经验法则。
11. The Producer shall 在 Phase 1 中**一次性**产出 `script.md` 与 `outline.md`（同一次思考），不拆为两个 checkpoint。

---

### 需求 4 - CHAPTER-CRAFT.md：章节实现单一入口

**用户故事：** 作为 Chapter Agent（subagent 或主代理），我希望在每章实现时只读一份 CHAPTER-CRAFT.md，覆盖原则 / 决策树 / 反 AI 味 / 代码红线 / 完工自检，避免长会话中遗忘原则。

#### 验收标准

1. The `references/CHAPTER-CRAFT.md` shall 是章节实现的**单一必读入口**，包含 8 个 Part：Part 0 十条原则 / Part 1 开工 5 问 / Part 2 关系→动作决策树 / Part 3 视觉工具箱 / Part 4 时长参考 / Part 5 反 AI 味反模式 / Part 6 代码硬规则 / Part 7 完工自检 / Part 8 反馈速查。
2. The Part 0 shall 列出 10 条原则：16:9 固定舞台 / 全局 step 计数器 / 每步独占整屏 / 口播节拍=step / 隐藏边角控件 / 舞台无 chrome / 内容驱动动画 / 多点逐个揭示 / 整片同一主题 / 双源原则。
3. The Part 5 shall 列出 AI 味反模式：紫粉/蓝紫渐变 / 圆角彩色边框 / emoji 当图标 / 假数据假 logo / 整章一种入场动画 / 持续闪烁 / 每屏角标。
4. The Part 6 shall 列出代码红线：必须用主题 token（颜色 + 字体家族） / `narrations.ts` 数组长度 = 章节 `if (step === N)` 最大 N + 1 / 章节物理隔离（独立文件夹 + 独立 CSS 类前缀 / `.cd-` `.wg-`）/ 不跨章 import / 完工跑 `npx tsc --noEmit`。
5. The Part 7 完工自检 shall 列出 12 项：每章 1-2 处视觉演示 / 不同 step 主导动作不一样 / 字号大留白舒服 / 清单逐个揭示 / 画面信息比口播多 / 无 AI 味反模式 / 无硬编码 hex / `narrations.ts` 长度对齐 / 每条 narration 与 script 语义一致 / 每 step 动画时长 ≤ 口播时长 / TypeScript 通过 / 无小号字体大量纯文字。
6. The CHAPTER-CRAFT.md shall 包含**硬性自检协议**：实现完成后必须走 自检 → 修复 → 汇报；禁止"实现完成 → 直接汇报给用户"。
7. The CHAPTER-CRAFT.md shall 提供"内容驱动动画"决策树：先找内在动作 → 找不到才入场动画兜底；持续微动慎用。
8. The Part 8 反馈速查 shall 提供常见用户反馈（动画太重 / 节奏太快 / 风格不对 / 信息太薄）的最小切片修复路径，禁止"重做整章"。

---

### 需求 5 - THEMES.md + 5 套主题资产

**用户故事：** 作为视频制作者，我希望 skill 自带 5 套精选主题，覆盖深色电影感 / 报刊 / 现代主义 / 终端 / 印刷五种气质，可直接通过脚手架参数选择。

#### 验收标准

1. The `references/THEMES.md` shall 完整描述主题系统：token 契约（颜色阶梯 / 字体家族 / 间距 / 圆角 / 分割线 / hero 数字 / 阴影 / 装饰 / 动效基线）+ 章节对 token 的两层消费规则（必须用 token 的 = 颜色+字体家族；自由发挥的 = 字号+间距+动画时长）。
2. The 5 套内置主题 shall 是：
   - `midnight-press` — 深色电影感编辑级（暖色 espresso + 火热橙）
   - `newsroom` — NYT 风报刊（报纸奶油 + 墨黑衬线 + 旗红）
   - `bauhaus-bold` — 现代主义（米白 + 墨黑 + 原色蓝 + 0 圆角）
   - `terminal-green` — 80s 磷光终端（纯黑 + JetBrains Mono + CRT 扫描线）
   - `monochrome-print` — 安静印刷杂志（米白 + 墨黑衬线 + 极简）
3. Each 主题 shall 包含 `themes/<id>/theme.json`（元数据）+ `themes/<id>/tokens.css`（CSS variables）。
4. The `theme.json` shall 包含字段：`id` / `nameZh` / `descriptionZh` / `bestFor: string[]`（脚本类型/语气匹配关键词）/ `mood`（电影感慢 / 弹簧 / 利落 / 安静）/ `palette`（深 vs 浅）。
5. The `tokens.css` shall 定义约 25-35 个 CSS 变量，覆盖：颜色阶梯（shell/surface/text/accent）+ 字体家族（display-cn/display-en/body/mono）+ 圆角性格（`--r-card`）+ 分割线性格（`--rule-w/--rule-style`）+ hero 数字风格（`--hero-num-*`）+ 装饰层（`--surface-pattern*` / `--surface-vignette` / `--text-shadow`）。
6. The `THEMES.md` shall 提供**创作新主题**流程：复制现有最接近主题 → 改 token + JSON → 跑 dev server 验证 → 加 `bestFor`。
7. The `THEMES.md` shall 强调**章节代码不得硬编码颜色 / 字体名**，只能用 token 或 primitive class。
8. The `THEMES.md` shall 列出 4 个 primitive class：`.hero-num` / `.rule` / `.card` / `.stage-frame`，每个 class 由当前主题的 token 决定其性格。

---

### 需求 6 - AUDIO.md：narrations.ts 中心 + mmx + qwen3 降级

**用户故事：** 作为视频制作者，我希望音频合成以每章 `narrations.ts` 为单一真相源，默认用 mmx-cli，未安装时自动降级到 qwen3 或交由用户选择 TTS。

#### 验收标准

1. The `references/AUDIO.md` shall 描述音频合成流程：扫所有 `narrations.ts` → 生成 `audio-segments.json` → 串行调 TTS → 落到 `public/audio/<id>/<step+1>.mp3`。
2. The `audio-segments.json` schema shall 是 `[{chapter, step, text, audio}]` 数组，对齐 `chapters.ts` 注册顺序。
3. The TTS 默认 shall 是 mmx-cli（MiniMax）；脚本 shall 检测 `which mmx`，未找到时进入降级路径。
4. The 降级路径 shall 提供 3 选项：(1) 帮用户安装 mmx-cli（含 npm 命令 + API key 获取链接）；(2) 用 qwen3（复用现有 `qwen3_tts_scene.py` 逻辑改造为读 segments）；(3) 用户自带 TTS（提供调用方式）。
5. The 合成脚本 shall **串行**调用避免 rate limit，**自动跳过已存在文件**（断点续合不烧重复 token）。
6. The 合成脚本 shall 在每条完成后打印进度，并在全部完成后跑 `ffprobe` 报告每条实际秒数，**重点关注 ≥ 15s 的条目**作为时长警告。
7. The `AUDIO.md` shall 列出**音频合成不动 outline.md** 原则——音频以 `narrations.ts` 为源，不回去读 outline 节选。
8. The `AUDIO.md` shall 提供故障排查表：mmx 未登录 / 401 / 中文音色不自然 / 单段过长被截断 / 音频 404 但 Auto 模式仍能跑 等场景。

---

### 需求 7 - RECORDING.md：Playwright 自动录屏 + OS 录屏路径

**用户故事：** 作为视频制作者，我希望 skill 提供两条录屏路径——Playwright 自动录屏（CI/无头化首选）+ OS 屏幕录制（手动场景），都能从 Auto 模式产出 MP4。

#### 验收标准

1. The `references/RECORDING.md` shall 在文档头列出两条路径决策矩阵：
   - **Playwright 自动录屏**：CI 集成 / 无头化 / 自动化批量产出
   - **OS 屏幕录制**：手动 demo / QuickTime / OBS / Cmd+Shift+5 / B 站推流软件
2. The Playwright 路径 shall 通过 `scripts/record-with-playwright.ts` 实现，接收参数：`<presentation-dir>` / `<output-mp4-path>` / `--viewport=1920x1080` / `--fps=30`。
3. The Playwright 脚本 shall 实现以下流程：
   - 启动 headless Chromium（带 GPU 加速）
   - `page.goto('http://localhost:5173/?auto=1')`
   - 等待字体加载完成（`document.fonts.ready` + 100ms 缓冲）
   - 等待 AutoStartGate 显示
   - 启动 `page.video()` 录制
   - 模拟按 SPACE 启动 Auto 模式
   - 等待 `[data-presentation-finished]` 事件
   - 停止录制
   - 用 ffmpeg 转 webm → mp4 + 裁掉头尾
4. The Playwright 脚本 shall 在录制开始前预热字体（让 Chromium 把所有 web fonts 完成 paint），避免首帧 fallback 字体。
5. The Playwright 脚本 shall 实现失败重试（最多 2 次）：录制中页面崩溃 / 音频加载失败时全片重录。
6. The Playwright 脚本 shall 在前端约定一个完成信号：每个章节最后一个 step 播完时在 DOM 上打 `data-presentation-finished="true"`。
7. The OS 录屏路径 shall 提供 mac / Windows / Linux 三平台的工具与设置（QuickTime / OBS / FFmpeg + xvfb）。
8. The `RECORDING.md` shall 提示：Playwright 路径有 **首帧黑屏 / 字体加载竞态 / 音频解码延迟** 三类潜在风险与缓解方案。

---

### 需求 8 - Vite + React 项目模板

**用户故事：** 作为 skill 用户，我希望 `templates/` 提供一个完整的 Vite + React + TypeScript 项目模板，脚手架命令一跑就能 dev server。

#### 验收标准

1. The `templates/` shall 包含完整的 Vite + React + TypeScript 项目骨架，可独立跑 `npm install && npm run dev`。
2. The 模板 shall 包含组件：`AutoStartGate`（Auto 模式 SPACE 启动蒙层）/ `AutoToggle`（手动 / Audio / Auto 三模式切换）/ `ProgressBar`（隐藏式底部进度条 + 章节跳转）/ `Stage`（16:9 固定舞台 + scale 适配）/ `MaskReveal`（基础动画原语）/ `SubtitleOverlay`（字幕条）。
3. The 模板 shall 包含 hooks：`useAudioPlayer`（audio.ended → next）/ `useAutoMode`（URL 参数 + M 键切换）/ `useStepper`（章节 + step 游标 + STORAGE_KEY 持久化）/ `useStageScale`（视口缩放）。
4. The 模板 shall 包含 5 套 primitive React 组件：`<HeroNum>`、`<Rule>`、`<Card>`、`<StageFrame>`、`<MaskReveal>`，主题性格通过 CSS class + token 自动接入。
5. The 模板 shall 在 `src/styles/` 包含：`base.css`（reset + 16:9 舞台基础样式）/ `tokens.css`（占位，由脚手架替换为选定主题）/ `animations.css`（共享 keyframes）/ `fonts.css`（Google Fonts import）。
6. The 模板 shall 包含 `src/registry/chapters.ts`（章节注册表，唯一允许跨章引用的文件）+ `src/registry/types.ts`（类型定义）。
7. The 模板 shall 包含 1 个示例章节 `src/chapters/01-example/` 含 `Example.tsx` + `Example.css` + `narrations.ts`，用户在脚手架后删除示例并替换为真实章节。
8. The 模板 shall 在 `App.tsx` 中实现：所有章节最后一个 step 播完时挂 `data-presentation-finished="true"` 到 `<body>` 上（供 Playwright 监听）。
9. The 模板 `package.json` scripts shall 包含：`dev` / `build` / `extract-narrations` / `synthesize-audio`。

---

### 需求 9 - scaffold.sh：一键脚手架

**用户故事：** 作为 skill 用户，我希望 `scripts/scaffold.sh <output-dir> --theme=<id>` 一行命令产出可跑的 Vite 项目。

#### 验收标准

1. The `scripts/scaffold.sh` shall 接收两个参数：`<output-dir>`（必填）+ `--theme=<theme-id>`（可选，默认 midnight-press）+ `--list-themes`（列出所有内置主题）。
2. The 脚手架 shall 复制 `templates/` 到 `<output-dir>`，并将选定主题的 `themes/<id>/tokens.css` 复制到 `<output-dir>/src/styles/tokens.css`。
3. The 脚手架 shall 在 `<output-dir>` 写入 `.theme` 文件记录主题 id（便于后续诊断）。
4. The 脚手架 shall 在结束后打印：`✓ Scaffolded at <dir>`、`Next: cd <dir> && npm install && npm run dev`、`Theme: <id>`。
5. The 脚手架 shall 校验 `<output-dir>` 不存在或为空，否则报错退出。
6. The `--list-themes` shall 读取 `themes/*/theme.json` 并按 nameZh + bestFor 列出，**不硬编码列表**。

---

### 需求 10 - narrations.ts 单一真相源契约

**用户故事：** 作为开发者，我希望每章 `narrations.ts` 是 step 数 + 字幕 + 音频的唯一真相源，避免 outline / 章节代码 / 音频文件三处漂移。

#### 验收标准

1. Each chapter folder `src/chapters/<NN>-<id>/` shall 包含 `narrations.ts`，导出 `narrations: string[]` 数组。
2. The `narrations.length` shall 等于章节代码 `if (step === N)` 出现的最大 N + 1。
3. The `narrations[i]` shall 是该 step 的口播文本（来自 `script.md` 对应段，语义一致，可微调标点适配 TTS）。
4. The 完全无音频的过场 step shall 用空串 `""`，Auto 模式按字数估时撑过。
5. The 章节代码、音频合成、运行时 stepper、字幕组件 shall 全部从 `narrations.ts` 推导 step 数与文本，**禁止任何地方手写 totalSteps**。
6. The `chapters.ts` 注册表 shall import 每章 `narrations` 并作为 `ChapterDef.narrations` 传入，不允许章节定义自己的 step 数。
7. The CHAPTER-CRAFT.md 完工自检 shall 包含 `narrations.ts` 长度对齐核查。
8. The `extract-narrations.ts` 脚本 shall 跨所有章节扫描 `narrations.ts`，按 `chapters.ts` 顺序生成 `audio-segments.json`，确保音频与代码不漂移。

---

### 需求 11 - 5-in-1 Checkpoint Plan

**用户故事：** 作为视频制作者，我希望 Phase 1 内容写完后只停一次，让我同时确认 5 件事——稿子 / outline / 主题 / 素材 / 开发模式——使 Phase 2 开始前所有关键决策已对齐。

#### 验收标准

1. When `script.md` 与 `outline.md` 都写完且自检通过, the SKILL.md shall 进入 Checkpoint Plan，向用户展示**单一**审核界面。
2. The Checkpoint Plan 输出 shall 包含 5 个对齐项（按顺序）：
   - **(1) 稿子**：`script.md` 字数 + 估时 + "要不要改"
   - **(2) 开发计划**：章节速览（id / 标题 / 步数 / 估时）+ "outline 要不要改"
   - **(3) 主题选择**：从 `themes/*/theme.json` 主动推荐 2-3 套（基于 `bestFor` 匹配脚本类型/语气）+ 列出剩余主题简介 + "也可让我帮你做新主题"
   - **(4) 素材准备**：粗看本视频要的图清单 + 三选项 a/b/c（路径挑选 / 用户提供 / 全 placeholder）
   - **(5) 开发模式**：A 逐章确认（默认）/ B 顺序 / C 并行（subagent，含并行数）
3. When 用户回复"主题你帮我选", the Producer shall 取推荐第 1 个，**告诉用户选了什么 + 为什么**，给反悔机会。
4. When 用户回复"开发模式你帮我选", the Producer shall 默认 A 模式并告知。
5. The Checkpoint Plan shall **不允许跳过**——即使所有项都用默认值，也要展示一次让用户有机会调整。
6. The Producer shall 在用户编辑 outline.md 后**重新解析**章节列表，更新内部状态，不重新生成 outline。
7. The Producer shall 在 Checkpoint Plan 通过后，把"5 件事的最终决定"写入 `presentation/.video-maker-state.yaml`（轻量级状态文件，仅供 skill 自身记录）。

---

### 需求 12 - 3 种开发模式 A / B / C

**用户故事：** 作为视频制作者，我希望根据视频规模与可用代理能力选择开发模式：A 逐章确认（默认）/ B 顺序开发 / C subagent 并行。

#### 验收标准

1. The SKILL.md shall 描述 3 种模式的差异、适用场景、风险：
   - **A 逐章确认**：第 2 章做完→暂停验收→第 3 章→...每章独立验收，风险最低
   - **B 顺序开发**：第 2~N 章主线程顺序做完，最后统一验收，速度中等
   - **C 并行 subagent**：第 2~N 章 subagent 并行，最快，但章节风格会有差异（这是预期）
2. **第 1 章无论哪种模式都必须主线程做完 + 用户验收**（强制 anchor）。
3. When 用户选 C 并行模式, the Producer shall 询问最大并行数（默认 4）。
4. The 并行模式 subagent prompt shall 包含：当前章节 outline 段落（含信息池）、`CHAPTER-CRAFT.md` 的路径（单一必读）、当前主题 `theme.json` 的 mood/bestFor（参考气质）、第 1 章代码作为代码风格参考（不是视觉抄袭对象）、硬规则（独立 CSS 前缀、不修改 `chapters.ts`、跑 `npx tsc --noEmit`）。
5. The 并行模式 shall 强制章节物理隔离：每章独立文件夹（`src/chapters/<NN>-<id>/`）+ 独立 CSS 类前缀（`.cd-` / `.wg-` / `.mg-`）+ 不跨章 import + 不修改 `chapters.ts` 之外的共享文件。
6. The 用户 shall 可以中途切换模式（"剩下的并行" / "剩下的逐章"）。
7. The SKILL.md shall 警告：并行模式下章节间风格差异是预期（"人手写视频的呼吸感 = 多 voice"）；如不可接受应选 A 或 B。

---

### 需求 13 - Chapter 1 Baseline 检查点

**用户故事：** 作为视频制作者，我希望第 1 章必须主线程做完 + 强制人审通过后才能继续，作为后续章节的风格锚。

#### 验收标准

1. When Phase 2 开始, the Producer shall 不论 dev_mode 是哪种, **第 1 章必须主线程实现**（不能 subagent / 不能跳过）。
2. The 第 1 章 shall 是**完整版本一次到位**：节奏 + 视觉 + 真素材齐全；**没有"骨架版"概念**。
3. When 第 1 章实现完成, the Producer shall 暂停在 dev server 处展示给用户验收。
4. The 验收提示 shall 包含 5 个核查重点：
   - 视觉气质对不对？符合 `<theme nameZh>` 的预期吗？
   - 节奏对不对？某些步太快/太慢/信息太薄？
   - 内容驱动动画是否到位？还是几步是无脑入场动画？
   - 双源原则：屏幕画面有没有"口播没念但 article 能挂"的细节？
   - 反 AI 味检查：紫粉渐变 / 圆角彩色边框 / 假插画 / emoji 是否有？
5. While 用户未确认基准通过, the Producer shall 拒绝构建剩余章节。
6. When 用户提供反馈, the Producer shall 仅修改第 1 章相关组件 + theme（如反馈涉及风格），不重写其他文件，重新展示后再次进入步骤 4。
7. When 用户回复"OK 继续" / "通过" / 类似肯定, the Producer shall 按选定 dev_mode 实现剩余章节。
8. The 第 1 章作为后续章节的"代码风格参考"shall 在 dev_mode = B/C 的 subagent prompt 中显式声明（不是视觉抄袭对象，是代码组织风格的对照）。

---

### 需求 14 - Reviewer Agent + 三层降级 + 修复后汇报铁律

**用户故事：** 作为内容质量负责人，我希望每个产出（script.md / outline.md / 单章实现）都走"独立 reviewer 核查 → 修复 → 再汇报"的硬性流程，避免代理"自评失真"。

#### 验收标准

1. The `agents/reviewer.md` shall 提供独立 Reviewer agent 的提示词，仅有读权限 + 写报告权限，禁止写入业务工件。
2. The Reviewer 执行方式 shall 按能力**三层降级**（按优先级依次尝试）：
   - **Tier 1 — Agent Teams**：开独立 reviewer agent，传入产出文件路径 + 清单 + 关键上下文
   - **Tier 2 — subAgent**：当前 agent 无 Teams 能力但能开 subagent
   - **Tier 3 — 当前 agent 自检**：兜底，**严格逐项**核查，不允许目测一遍就放行
3. The Reviewer 三层降级 shall 在 SKILL.md 与 references 中**重复出现**（关键节点明确写"按能力降级"），保证代理在长会话中也能命中规则。
4. The Reviewer 报告 shall 是结构化输出：每项 `pass | warn | fail` + `evidence` + `suggested_fix`。
5. **铁律**：拿到结论后**先按 fail 项把产出改完**，再向用户汇报"做完了 + 自检结论 + 改了什么"。**直接拿原始结论汇报但不修复 = 违规**。
6. The 三个 ratify checklist shall 存在：
   - `ratify/reviewer-script-checklist.md`（脚本核查：信息保留 / 形式 / 风骨 / 念出来）
   - `ratify/reviewer-outline-checklist.md`（outline 核查：信息池来源 / step 单行 / 时长累加 / 章节切分）
   - `ratify/reviewer-project-checklist.md`（项目核查：每章视觉演示 / 反 AI 味 / token 一致 / narrations 对齐 / TypeScript 通过）
7. The Reviewer 触发点 shall 是：script.md 写完后 / outline.md 写完后 / 第 1 章实现后 / 各章实现后 / 全部章节完工后。
8. When Reviewer 自身执行失败（超时 / tool error）, the Producer shall 视为 warning（不阻断），在状态中记录 `reviewer_unavailable: <reason>`。

---

### 需求 15 - Playwright 自动录屏脚本

**用户故事：** 作为 CI/自动化使用者，我希望 `scripts/record-with-playwright.ts` 脚本能在无头环境下从 Vite 项目自动产出 MP4。

#### 验收标准

1. The `scripts/record-with-playwright.ts` shall 是独立可执行的 Node.js 脚本（用 `tsx` 或 `node --experimental-strip-types`）。
2. The 脚本 shall 接收参数：`<presentation-dir>` / `--output=<path.mp4>` / `--viewport=1920x1080` / `--fps=30` / `--retries=2`。
3. The 脚本 shall 自动跑 `npm run build && npm run preview` 启动生产 server（避免 dev mode HMR 干扰录制），等待 server 就绪后再开始录制。
4. The 脚本 shall 在录制前**预热**：等待 `document.fonts.ready` + 100ms 缓冲 + 等待 AutoStartGate 元素挂载。
5. The 脚本 shall 在监听 `data-presentation-finished="true"` 后停止录制，并报告总时长。
6. The 脚本 shall 自动跑 `ffmpeg` 把 webm 转 mp4（H.264 + AAC），裁掉头部 SPACE 触发的 200ms 黑屏。
7. The 脚本 shall 实现失败重试：录制中页面崩溃 / 音频加载失败 / Playwright timeout 时全片重录最多 N 次（默认 2）。
8. The 脚本 shall 在结束时打印：`✓ Recorded: <output>` + `Duration: Xs` + `Size: YMB`。
9. The 脚本 shall 在 `package.json` 中添加 `record` script：`"record": "tsx scripts/record-with-playwright.ts"`。
10. The 脚本 shall **不依赖** DeepAgents Python 工具链，可独立通过 Node.js 跑（阶段 1 的核心约束）。

---

### 需求 16 - 端到端 Demo（Anthropic 博客）

**用户故事：** 作为 skill 验证者，我希望阶段 1 完成后能用一篇 Anthropic 真实博客文章端到端跑通完整流程（Phase 1 → 4），产出 1 个真实 MP4 作为验收物。

#### 验收标准

1. The `demos/anthropic-article-demo/` 目录 shall 包含一次真实端到端运行的全部产物：
   - `article.md`（Anthropic 博客原文）
   - `script.md`（Phase 1.2 产出）
   - `outline.md`（Phase 1.2 产出，含 ≥ 3 个章节）
   - `presentation/`（Vite 项目，含 ≥ 3 章实现 + 主题应用 + 真实合成的 audio）
   - `final.mp4`（Playwright 录屏产物 OR 手动录屏）
2. The demo 选用的文章 shall 是 Anthropic 官方博客中**近 6 个月**的某篇技术/产品文章（具体哪篇由实施时挑选），**作为 fair use 引用使用**。
3. The demo 跑通 shall 验证以下方法论落地：
   - 双源原则：article.md 保留 + outline 信息池 ≥ 3 条 + 画面信息 > 口播信息
   - SCRIPT-STYLE：信息保留 ≥ 60% + 念出来测试通过
   - 主题应用：从 5 套主题中选 1 套，章节代码无硬编码颜色/字体
   - narrations.ts 单源：所有章节 step 数与代码一致
   - 章节物理隔离：每章独立 CSS 前缀
   - Reviewer 跑过：3 份 reviewer-*-run-1.json 报告齐全
   - Playwright 录屏：1 个 MP4 输出
4. The demo 目录 shall 包含 `RUN-LOG.md`，记录端到端运行的关键节点：哪一步用了多久 / 哪些 reviewer item 报了 fail / 修复花了多少轮 / 最终 MP4 时长。
5. The demo shall 作为后续阶段 2（DeepAgents 集成）的回归测试基线。
6. The demo 完成 shall 是阶段 1 的**结项验收标志**——demo 跑通 = 阶段 1 完成。

---

### 需求 17 - skills/video-maker-v2/ 标记 deprecated

**用户故事：** 作为仓库维护者，我希望旧的 `skills/video-maker-v2/`（Remotion 路线）在新 skill 上线后明确标记为 deprecated，避免代理继续命中旧 skill。

#### 验收标准

1. When 阶段 1 完成（demo 跑通）, the `skills/video-maker-v2/SKILL.md` 的 frontmatter description shall 加前缀 `[DEPRECATED]` 并在文档头部加段落说明：
   - 已被 `skills/video-maker/`（Web 录屏路线）替代
   - 路线决策依据：参考 `specs/video-maker-web-port/`
   - deprecation 时间戳与目标删除时间（阶段 2 完成后删除）
2. The `skills/video-maker-v2/manifest.json` 的 description 字段 shall 加 `[DEPRECATED]` 前缀。
3. The `CLAUDE.md`（项目根级）shall 增加段落标注：`skills/video-maker/` 为当前推荐路径；`skills/video-maker-v2/` 仅供参考，不要新启会话使用。
4. The `.deepagents/skills/video-maker-v2-*` 子目录 shall 不动（保留以便 DeepAgents 集成层在阶段 2 处理时仍能加载，避免破坏）。
5. The `tests/deepagents_video_maker/test_skill_files.py` 中相关断言 shall **暂不修改**（阶段 2 一并处理），但要确保新 skill 的存在不破坏现有测试。
6. The 旧 skill 的实际删除 shall 推迟到阶段 2，避免阶段 1 实施期破坏正在跑的测试与 DeepAgents 集成层。

---

### 需求 18 - skill 内嵌 manifest 校验脚本

**用户故事：** 作为 skill 维护者，我希望 `skills/video-maker/scripts/validate-skill.sh`（或 `.ts`）能在 commit 前/CI 中自动校验 skill 自身的完整性，避免 references 文件缺失、主题资产残缺、模板损坏、frontmatter 字段不一致等"破坏可分发性"的问题悄然进入 main 分支。

#### 验收标准

1. The `skills/video-maker/scripts/validate-skill.sh` shall 是 skill 内嵌的自检脚本，可独立执行（不依赖项目根 `package.json` 或 DeepAgents 工具链）。
2. The 脚本 shall 校验 `manifest.json` schema：必填字段（`name` / `version` / `category` / `description` / `compat`）存在且类型正确；`compat` 是字符串数组；`name === "video-maker"`。
3. The 脚本 shall 校验 `SKILL.md` frontmatter：必须以 `---\n` 开头；包含 `name: video-maker`；`description` 字段存在且非空；与 `manifest.json.name` 一致。
4. The 脚本 shall 校验 6 份 references 全部存在：`SCRIPT-STYLE.md` / `OUTLINE-FORMAT.md` / `CHAPTER-CRAFT.md` / `THEMES.md` / `AUDIO.md` / `RECORDING.md`，每份 ≥ 100 字（防止占位空文件）。
5. The 脚本 shall 校验 5 套主题资产完整：每个 `themes/<id>/` 同时包含 `theme.json` + `tokens.css`；`theme.json` 必填字段（`id` / `nameZh` / `descriptionZh` / `bestFor` / `mood` / `palette`）存在；`id` 与目录名一致。
6. The 脚本 shall 校验 ratify checklist 三份齐全：`ratify/reviewer-script-checklist.md` / `reviewer-outline-checklist.md` / `reviewer-project-checklist.md`。
7. The 脚本 shall 校验 `agents/reviewer.md` 存在且 ≥ 50 字。
8. The 脚本 shall 校验 `templates/` 完整性：`package.json` / `vite.config.ts` / `src/App.tsx` / `src/registry/chapters.ts` / `src/registry/types.ts` / `src/styles/base.css` / `src/styles/tokens.css`（占位）/ `src/chapters/01-example/{Example.tsx,Example.css,narrations.ts}` 全部存在。
9. The 脚本 shall 校验 `scripts/` 中 4 个核心脚本存在：`scaffold.sh` / `extract-narrations.ts` / `synthesize-audio.sh` / `record-with-playwright.ts`。
10. The 脚本 shall 在所有校验通过时退出码 0 并打印 `✓ skill validation passed (M files / N themes / K references)`；失败时退出码 1 并逐条列出失败项与修复建议。
11. The 脚本 shall 用 bash 实现（不依赖 Node.js / Python），保证任何环境可跑；如必须用 Node.js（例如解析 JSON 复杂逻辑），则用纯 stdlib `node`，不引入 npm 依赖。
12. The 项目根级 `package.json` shall 增加 script：`"skill:validate": "bash skills/video-maker/scripts/validate-skill.sh"`，方便 `pnpm skill:validate` 调用。
13. The skill validation shall 不挂在任何 git pre-commit hook（保持"显式调用"），但建议在 README.md 中说明"提 PR 前请跑一次"。
14. When 阶段 1 实施期, the 每个需求实现完成后 shall 跑一次 `pnpm skill:validate` 作为 sanity check（在 tasks.md 中显式列入）。

---

## 范围说明

**包含**（阶段 1）：

- 移除 better-harness 基础设施
- 新建 `skills/video-maker/` 目录骨架
- 6 份 references 文档（SCRIPT-STYLE / OUTLINE-FORMAT / CHAPTER-CRAFT / THEMES / AUDIO / RECORDING）
- 5 套主题资产（theme.json + tokens.css）
- 1 个 Reviewer agent 提示词 + 3 份 ratify checklist
- Vite + React 项目模板（含 hooks / components / primitives / styles / 示例章节）
- `scaffold.sh` + `extract-narrations.ts` + `synthesize-audio.sh` + `record-with-playwright.ts`
- **`validate-skill.sh` 内嵌校验脚本**
- Anthropic 博客端到端 demo
- 旧 `skills/video-maker-v2/` 标记 deprecated（不删除）

**不包含**（推到阶段 2）：

- DeepAgents Python 工具层适配（`vm_*` LangChain tools）
- `state.yaml` / `goal.yaml` Python 解析器
- `tests/deepagents_video_maker/` 全面改造
- `skills/video-maker-v2/` 实际删除
- `src/deepagents_video_maker/` 现有 Remotion 相关代码清理
- `agents/scriptwriter.md` 与 `agents/remotion-builder.md` 与新 skill 的派发兼容
- Producer agent factory 改动

---

## 待确认问题

1. **demo 文章具体选哪篇 Anthropic 博客**：实施时再挑，还是现在就定？建议实施时再挑（基于当时最近发布的内容）。
2. **`templates/` 是 npm package 还是直接拷贝目录**：直接拷贝目录（与 web-video-presentation 一致），不上 npm。
3. **`record-with-playwright.ts` 的 Playwright 版本**：用 latest stable（写需求时是 1.45+）。
4. **5 套主题中每套是否都需要 `mood` 字段对应到具体 ms 值的建议表**：建议在 THEMES.md 文末提供一个 `mood → 时长建议范围` 的非强制参考表。
5. ~~**是否要在 skill 内嵌一个 manifest 校验脚本**：阶段 1 暂不做，阶段 2 加。~~ → **已采纳：阶段 1 必须实现**（见需求 18）。
