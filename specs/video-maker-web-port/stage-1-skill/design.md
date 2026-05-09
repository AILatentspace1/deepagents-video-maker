# 技术方案设计 — Stage 1: video-maker Skill 本体（Web 录屏路线）

## 0. 设计前提

### 0.1 已采纳的决策（来自 brainstorming）

| 维度 | 决策 |
|---|---|
| 路线 | 路线 1：完全转向 Web 录屏（fork 方法论 + 重写 skill） |
| 阶段策略 | 阶段 1 = skill 本体可端到端跑；阶段 2 = DeepAgents 集成 |
| Q1 目录命名 | B：`skills/video-maker/`（新）+ `skills/video-maker-v2/`（旧标 deprecated）并存 |
| Q2 attribution | B：方法论参考 web-video-presentation，**自行重写**所有 skill 文件 |
| Q3 demo 文章 | A：实施时再挑某篇 Anthropic 博客 |
| Q4 旧 spec 处置 | B：原文件加 `.deprecated.md` 后缀（已执行） |

### 0.2 已采纳的待确认问题答案

| Q | 答案 |
|---|---|
| 1. demo 文章哪篇 | 实施时挑（基于当时最新发布） |
| 2. templates 形式 | 直接拷贝目录，不上 npm |
| 3. Playwright 版本 | latest stable（1.45+） |
| 4. THEMES.md mood→时长建议表 | 提供，**非强制** |
| 5. manifest 校验脚本 | **阶段 1 实现**（需求 18） |

### 0.3 核心设计原则

1. **skill 自洽** — 不依赖项目其他目录、不依赖 DeepAgents、不依赖 Python；任何 Claude Code / Cursor / Codex 用户安装即可用
2. **方法论 100% 保真** — web-video-presentation 经验全部移植，但文字自行重写
3. **可分发** — `skills/video-maker/` 整个目录可拷贝到任意位置当独立 skill
4. **可校验** — `validate-skill.sh` 在每次改动后能跑通

---

## 1. skill 文件树详细 schema

```
skills/video-maker/
├── SKILL.md                                # 主入口；frontmatter + 4 Phase + 各阶段读取指南
├── README.md                               # 英文入门 + 安装步骤
├── README.zh-CN.md                         # 中文入门 + 安装步骤
├── manifest.json                           # name/version/category/description/compat
│
├── references/                             # 长文 references，按阶段查阅
│   ├── SCRIPT-STYLE.md                     # 信息保留 ≥ 60% + 8 形式 + 5 风骨 + 念出来测试
│   ├── OUTLINE-FORMAT.md                   # 人类可编辑 + 信息池 + 不写动画
│   ├── CHAPTER-CRAFT.md                    # 章节实现单一入口（8 Part）
│   ├── THEMES.md                           # 主题 token 契约 + 5 套主题清单 + 创作流程
│   ├── AUDIO.md                            # narrations.ts 中心 + mmx + qwen3 降级
│   ├── RECORDING.md                        # Playwright 自动录屏 + OS 录屏路径
│   └── EXAMPLES/                           # 章节结构示例（不是抄袭模板）
│       ├── README.md
│       ├── hook-chapter/                   # 钩子型开场结构
│       │   ├── README.md
│       │   ├── chapter.tsx
│       │   └── chapter.css
│       ├── list-reveal/                    # 列举型逐个揭示
│       └── case-tech-review/               # 案例对比型
│
├── agents/
│   └── reviewer.md                         # 独立 Reviewer agent 提示词
│
├── ratify/
│   ├── reviewer-script-checklist.md        # 脚本核查清单
│   ├── reviewer-outline-checklist.md       # outline 核查清单
│   └── reviewer-project-checklist.md       # 项目核查清单
│
├── themes/                                 # 5 套主题资产
│   ├── midnight-press/
│   │   ├── theme.json                      # nameZh/descriptionZh/bestFor/mood/palette
│   │   └── tokens.css                      # 25-35 个 CSS 变量
│   ├── newsroom/
│   ├── bauhaus-bold/
│   ├── terminal-green/
│   └── monochrome-print/
│
├── scripts/
│   ├── scaffold.sh                         # 一键脚手架（带 --theme / --list-themes）
│   ├── extract-narrations.ts               # 扫所有 narrations.ts → audio-segments.json
│   ├── synthesize-audio.sh                 # mmx 优先 + qwen3 降级
│   ├── record-with-playwright.ts           # 自动录屏
│   └── validate-skill.sh                   # skill 内嵌完整性校验
│
└── templates/                              # Vite + React + TS 项目模板（脚手架复制源）
    ├── package.json                        # 含 dev/build/preview/extract-narrations/synthesize-audio/record
    ├── tsconfig.json
    ├── vite.config.ts
    ├── index.html
    ├── public/                             # 占位
    └── src/
        ├── main.tsx                        # React root mount
        ├── App.tsx                         # 主应用：Stage + ProgressBar + AutoToggle + AutoStartGate
        ├── components/                     # 共享组件
        │   ├── AutoStartGate.tsx
        │   ├── AutoStartGate.css
        │   ├── AutoToggle.tsx
        │   ├── AutoToggle.css
        │   ├── ProgressBar.tsx
        │   ├── ProgressBar.css
        │   ├── Stage.tsx
        │   ├── SubtitleOverlay.tsx
        │   └── MaskReveal.tsx              # 基础动画原语
        ├── primitives/                     # 5 套主题性格 primitive 组件
        │   ├── HeroNum.tsx
        │   ├── Rule.tsx
        │   ├── Card.tsx
        │   └── StageFrame.tsx
        ├── hooks/
        │   ├── useAudioPlayer.ts           # audio.ended → onAutoAdvance
        │   ├── useAutoMode.ts              # URL ?auto=1 + M 键
        │   ├── useStepper.ts               # 章节 + step 游标 + STORAGE_KEY
        │   └── useStageScale.ts            # 1920×1080 → viewport scale
        ├── registry/
        │   ├── chapters.ts                 # 唯一允许跨章引用
        │   └── types.ts                    # ChapterDef / ChapterStepProps / Narration
        ├── styles/
        │   ├── base.css                    # reset + 16:9 舞台基础
        │   ├── tokens.css                  # 占位（脚手架替换为选定主题）
        │   ├── animations.css              # 共享 keyframes
        │   └── fonts.css                   # Google Fonts import
        └── chapters/
            └── 01-example/                 # 示例章节，脚手架后用户删除
                ├── Example.tsx
                ├── Example.css
                └── narrations.ts
```

---

## 2. 5 套主题"DNA 一句话锚点"

每套主题在写 `tokens.css` 前，先用一句话钉死它的视觉 DNA，避免施工期发散。

| 主题 id | DNA 一句话锚点 | 关键签名 token |
|---|---|---|
| `midnight-press` | 暖色 espresso 深色，Instrument Serif 斜体英文对 Noto Serif SC 中文，电影感慢节奏（1.6s 揭示），只有 vignette 没颗粒 | `--shell: #1a120c; --accent: #ff6b35; --hero-num-style: italic-serif; --r-card: 4px; --rule-w: 1px solid` |
| `newsroom` | NYT 报刊，纸黄底 + 墨黑衬线 + 旗红 accent，Playfair Display + Noto Serif SC，0 圆角（报纸不会圆角） | `--shell: #f4ede0; --text: #1a1612; --accent: #c8102e; --hero-num-style: italic-display-serif; --r-card: 0` |
| `bauhaus-bold` | 现代主义宣言，米白 + 墨黑 + 原色蓝，Archivo Black + Inter，0 圆角 + 4px 实色厚边 + 偏移实色阴影，font-weight 900 巨字 | `--shell: #f5f1e8; --accent: #0033cc; --r-card: 0; --rule-w: 4px solid; --shadow-stage: 8px 8px 0 #1a1a1a` |
| `terminal-green` | 80s 磷光终端，纯黑 + JetBrains Mono only + 0 直角，CRT 扫描线贴在舞台，磷光 text-shadow，利落 180/400/650ms | `--shell: #000000; --text: #00ff41; --r-card: 0; --surface-pattern: repeating-linear-gradient(...); --text-shadow: 0 0 10px #00ff41` |
| `monochrome-print` | 安静精炼印刷杂志（Monocle 风），米白 + 墨黑衬线 + 墨蓝 accent，Source Serif，1px 实线发丝 + 4px 精炼圆角，无装饰极静（1.7s 揭示） | `--shell: #f8f6f2; --text: #1a1a1a; --accent: #1a3a6c; --r-card: 4px; --rule-w: 1px solid; --surface-pattern: none` |

每套主题 `theme.json` schema：

```json
{
  "id": "midnight-press",
  "nameZh": "午夜印刷",
  "descriptionZh": "电影感深色编辑级。暖色 espresso 不是纯黑。Instrument Serif 斜体英文对 Noto Serif SC 中文。慢速电影感节奏。",
  "bestFor": ["技术深度", "产品发布", "故事讲述", "深沉叙事"],
  "mood": "cinematic-slow",
  "palette": "dark"
}
```

`mood` 枚举与建议时长（THEMES.md 末尾的非强制参考表）：

| mood | 揭示动画建议 ms | 错峰间隔建议 ms |
|---|---|---|
| `cinematic-slow` | 1400-1800 | 200-400 |
| `editorial-quiet` | 1200-1700 | 150-350 |
| `crisp-linear` | 180-450 | 60-120 |
| `springy` | 600-900 (with overshoot) | 100-200 |
| `bold-modernist` | 250-500 | 80-150 |

---

## 3. Vite 项目模板架构

### 3.1 数据流

```
URL ?auto=1
  ↓
useAutoMode → mode: "auto"
  ↓
AutoStartGate 显示蒙层 → 用户按 SPACE → autoStarted=true
  ↓
useStepper.cursor = { chapter: 0, step: 0 }
  ↓
App.tsx 渲染 <Cmp step={cursor.step} />
  ↓
useAudioPlayer({ src: /audio/<id>/<step+1>.mp3, mode: "auto", autoStarted, ...})
  ↓
audio.play() → audio.ended (+ trailMs)
  ↓
onAutoAdvance() → stepper.next()
  ↓
cursor.step++（或跨章 cursor.chapter++ + cursor.step=0）
  ↓
（重复）...
  ↓
最后一章最后一个 step 结束
  ↓
App.tsx 在 <body> 上挂 data-presentation-finished="true"
  ↓
Playwright 监听到该属性 → 停止录制
```

### 3.2 关键 hooks 职责

| hook | 输入 | 输出 | 职责 |
|---|---|---|---|
| `useStepper` | `CHAPTERS: ChapterDef[]` | `{ cursor, next, prev, jumpToChapter }` | 章节 + step 游标管理；`STORAGE_KEY` 持久化（避免刷新丢游标）；最后 step 后挂 `data-presentation-finished` |
| `useAudioPlayer` | `{ src, mode, trailMs, estimateFallbackMs, onAutoAdvance, autoStarted }` | （无；副作用：播放 + 推进） | 单 hidden audio 元素；audio.ended → trailMs → onAutoAdvance；error/missing → estimateFallbackMs 兜底 |
| `useAutoMode` | URL params | `{ mode, cycleMode, autoStarted, setAutoStarted }` | 解析 `?auto=1` / `?audio=1`；监听 M 键切换 |
| `useStageScale` | `containerRef` | `{ scale }` | 1920×1080 内容 + transform scale 适配任意 viewport |

### 3.3 primitive 组件职责

每个 primitive 是 React functional component，主题性格通过 CSS class + token 自动接入：

```typescript
// HeroNum.tsx
export function HeroNum({ children, ...rest }: HTMLAttributes<HTMLSpanElement>) {
  return <span className="hero-num" {...rest}>{children}</span>;
}
```

```css
/* base.css */
.hero-num {
  font-family: var(--font-display-en);
  font-style: var(--hero-num-font-style, normal);
  font-weight: var(--hero-num-font-weight, 700);
  font-feature-settings: var(--hero-num-feature-settings, "tnum");
  letter-spacing: var(--hero-num-letter-spacing, -0.02em);
}
```

主题在 `tokens.css` 中重写这些变量，hero-num 自动变成不同性格。

### 3.4 章节代码模式

```typescript
// src/chapters/02-coldopen/Coldopen.tsx
import { HeroNum, Rule, MaskReveal } from "../../primitives";
import "./Coldopen.css";

export default function Coldopen({ step }: ChapterStepProps) {
  if (step === 0) {
    return (
      <div className="cd-scene">
        <MaskReveal show duration={900}>
          <h1 className="cd-h">先说一个数字</h1>
        </MaskReveal>
      </div>
    );
  }
  if (step === 1) {
    return (
      <div className="cd-scene cd-stat">
        <HeroNum>3.4×</HeroNum>
        <Rule />
        <p className="cd-caption">推理速度提升</p>
      </div>
    );
  }
  // ...
}
```

```typescript
// src/chapters/02-coldopen/narrations.ts
export const narrations: string[] = [
  "我先给你看一个数字",      // step 0
  "三点四倍。这是新模型的推理速度提升",  // step 1
  // ...
];
```

`if (step === N)` 的最大 N + 1 必须 = `narrations.length`，由 CHAPTER-CRAFT.md 完工自检 + Reviewer project 清单核对。

### 3.5 章节物理隔离硬规则

- 文件夹：`src/chapters/<NN>-<id>/`
- CSS 类前缀：每章选一个 2-3 字母前缀（`.cd-` / `.wg-` / `.mg-` / `.pm-`）
- 不允许 `import` 跨章节文件（除从 `registry/types`、`primitives/*`、`components/*`）
- 不允许修改 `chapters.ts` 之外的共享文件
- 完工跑 `npx tsc --noEmit`

并行 subagent 模式下这些规则成为**强制约束**写入 prompt。

---

## 4. narrations.ts 真相源传递链路

```
┌─────────────────────────────────────┐
│ src/chapters/<NN>-<id>/narrations.ts│
│   export const narrations = [...]   │  ← 真相源
└──────────────┬──────────────────────┘
               │
       ┌───────┴────────┬──────────────┬─────────────┐
       │                │              │             │
       ▼                ▼              ▼             ▼
chapters.ts       SubtitleOverlay   useStepper   extract-narrations.ts
(import +         (从 narrations[]  (length 决定  (扫所有章节 →
 注册)            取当前 step 文本)  totalSteps)   audio-segments.json)
                                                       │
                                                       ▼
                                                 synthesize-audio.sh
                                                 (mmx/qwen3 → public/audio/)
                                                       │
                                                       ▼
                                                 useAudioPlayer
                                                 (按约定路径加载 mp3)
```

5 处一致性来自唯一真相源，不允许任何地方手写 `totalSteps`。

`extract-narrations.ts` 实现：

```typescript
// 伪代码
import { CHAPTERS } from "../src/registry/chapters";

const segments = CHAPTERS.flatMap((chapter, ci) =>
  chapter.narrations.map((text, si) => ({
    chapter: chapter.id,
    step: si + 1,
    text,
    audio: `${chapter.id}/${si + 1}.mp3`,
  }))
);

writeFileSync("audio-segments.json", JSON.stringify(segments, null, 2));
```

---

## 5. Playwright 录屏脚本架构

### 5.1 完整流程

```
1. 启动 Vite preview server (背景进程，端口 4173)
   │
2. 健康检查：curl http://localhost:4173 200 OK
   │
3. playwright.chromium.launch({
     headless: true,
     args: ['--enable-gpu', '--use-gl=angle', '--disable-software-rasterizer']
   })
   │
4. browser.newContext({
     viewport: { width: 1920, height: 1080 },
     recordVideo: { dir: './recordings/', size: { width: 1920, height: 1080 } }
   })
   │
5. page.goto('http://localhost:4173/?auto=1')
   │
6. await page.waitForLoadState('networkidle')
   │
7. 字体预热：await page.evaluate(() => document.fonts.ready)
   │
8. await page.waitForTimeout(200)  // 字体绘制缓冲
   │
9. await page.waitForSelector('[data-auto-start-gate]', { state: 'visible' })
   │
10. await page.keyboard.press('Space')
    │
11. await page.waitForSelector('[data-presentation-finished="true"]', {
      state: 'attached',
      timeout: <根据章节数估算>
    })
    │
12. await page.waitForTimeout(500)  // 让最后一帧定格
    │
13. await page.close() → video 保存为 webm
    │
14. ffmpeg -i recordings/<hash>.webm
        -ss 0.2 -c:v libx264 -preset slow -crf 18
        -c:a aac -b:a 192k
        -r <fps> output.mp4
    │
15. ✓ Recorded: <output> | Duration: Xs | Size: YMB
```

### 5.2 失败模式与重试

| 失败模式 | 检测 | 重试策略 |
|---|---|---|
| Vite server 启动失败 | port 检查超时 | 不重试，报错退出 |
| 字体加载竞态（fallback 字体进入第一帧） | 第 7-8 步等待 | 已通过 `document.fonts.ready` + 200ms 缓冲缓解；不重试 |
| AutoStartGate 没出现 | 第 9 步 selector timeout | 重试整段录制（最多 N 次） |
| 录制中页面崩溃 | playwright crash event | 重试整段录制 |
| 音频加载 404 | console.error 监听 | 不阻断（useAudioPlayer 退化估时），但记 warning |
| `data-presentation-finished` 长时间不挂 | 第 11 步 timeout | 重试整段录制 |
| ffmpeg 转码失败 | exit code ≠ 0 | 不重试，保留 webm 报错 |

重试默认 2 次，可通过 `--retries=N` 调。

### 5.3 完成信号约定（前后端契约）

`templates/src/App.tsx` 在 `useStepper` 推进到末尾时挂标记：

```typescript
useEffect(() => {
  if (stepper.isFinished) {
    document.body.dataset.presentationFinished = "true";
  }
}, [stepper.isFinished]);
```

`useStepper` 暴露 `isFinished: boolean`：

```typescript
const isFinished =
  cursor.chapter === CHAPTERS.length - 1 &&
  cursor.step === CHAPTERS[CHAPTERS.length - 1].narrations.length - 1 &&
  hasAdvancedPastFinalStep;
```

---

## 6. Reviewer 三层降级实现

### 6.1 Tier 选择规则

```
Producer 准备调度 Reviewer 时：

if (具备 Agent Teams 能力 / 显式开了 Teams)
  → Tier 1：spawn 独立 reviewer agent，传 (产出文件路径 + 清单 + 上下文)
elif (能开 subagent / Task tool 可用)
  → Tier 2：用 subagent 走同流程
else
  → Tier 3：当前 agent 严格逐项核查，禁止"目测一遍"

无论哪一 Tier，输出格式相同：reviewer-*-run-N.json
```

### 6.2 Tier 1 / Tier 2 调度 prompt 结构

```
你是独立 Reviewer，仅有读权限 + 写 reviewer-<id>-run-<N>.json 权限。
禁止修改业务工件。

输入：
- 待核查产出：<file-path>
- 清单：<checklist-path>
- 上下文（不必要不读）：<context-paths>

工作流：
1. 读清单
2. 逐项核查产出
3. 每项标注 pass | warn | fail + evidence + suggested_fix
4. 写入 <report-path>，结构化 JSON
5. 报告自身执行成功/失败给 Producer

铁律：
- 不允许"产出看起来 OK 就 pass"，必须有 evidence
- 不确定的标 warn 而非 pass
```

### 6.3 Tier 3 自检的"严格"约束

`SKILL.md` 在每个 Reviewer 触发点都写：

> 优先 Tier 1 → Tier 2 → Tier 3。Tier 3 兜底时必须**严格逐项**写出 evidence，禁止用"我看了一遍 OK"代替。

### 6.4 修复后汇报铁律

`SKILL.md` 在每个 Reviewer 触发点都写一段：

> **铁律**：Reviewer 出 fail 项后，**先按 fail 项修复产出**，修复完再向用户汇报"做完了 + 自检结论 + 改了什么"。**直接把 reviewer 报告原文丢给用户但没修复 = 违规**。

实现层面这一条不需要 Python 代码，纯 prompt 约束 —— 但在 `agents/reviewer.md` 与 `SKILL.md` 至少各重复一次，长会话也能命中。

### 6.5 Reviewer 报告 JSON schema

```json
{
  "checklist_id": "script | outline | project",
  "run_number": 1,
  "started_at": "2026-05-09T20:00:00Z",
  "finished_at": "2026-05-09T20:01:30Z",
  "tier_used": "agent_teams | subagent | self_check",
  "overall_status": "pass | warn | fail",
  "items": [
    {
      "id": "script.information_retention",
      "category": "structure | fidelity | style",
      "status": "pass | warn | fail",
      "evidence": "len(script.md)=2400, len(article.md)=4000, ratio=0.60 OK",
      "suggested_fix": null
    }
  ]
}
```

---

## 7. mmx + qwen3 + 自带 TTS 统一接入

### 7.1 接入接口（最小契约）

任何 TTS 后端只要能满足三件事：

| 能力 | 输入 | 输出 |
|---|---|---|
| 单段合成 | text (≤ 5000 字) + voice_id (可选) + output_path | mp3/wav 文件 |
| 错误反馈 | — | exit code ≠ 0 + stderr 明确报错 |
| 输出可指定路径 | output_path | 文件直接落到该路径 |

### 7.2 `synthesize-audio.sh` 决策树

```bash
# 伪代码
which mmx
if [ $? -eq 0 ]; then
  ENGINE="mmx"
  CMD='mmx speech synthesize --text "$TEXT" --output "$OUT"'
elif [ -f "../../scripts/qwen3_tts_scene.py" ]; then
  ENGINE="qwen3"
  CMD='uv run python ../../scripts/qwen3_tts_scene.py --text "$TEXT" --output "$OUT"'
else
  echo "Neither mmx nor qwen3 detected. Options:"
  echo "  1. Install mmx: npm install -g mmx-cli"
  echo "  2. Bring your own TTS (edit synthesize-audio.sh CMD line)"
  exit 1
fi

# 串行 + 跳过已存在
for segment in $(jq -r ... audio-segments.json); do
  TEXT=...; OUT=...
  if [ -f "$OUT" ]; then
    echo "skip $OUT"
    continue
  fi
  eval $CMD
done
```

注：阶段 1 中 `qwen3_tts_scene.py` 仍在 `scripts/` 下（来自 v2.0），阶段 1 不动它，但 `synthesize-audio.sh` 知道怎么调用它（向上回溯 `../../scripts/`）。阶段 2 决定是否复制进 skill 内。

### 7.3 mmx 鉴权检查

```bash
mmx auth status
# 未登录则提示：
#   你的 mmx-cli 未登录。请运行：
#     mmx auth login --api-key sk-xxxxx
#   API key 在 https://platform.minimaxi.com 获取
```

---

## 8. validate-skill.sh 实现

### 8.1 实现策略

纯 bash + 标准 Unix 工具（`test`、`jq`、`wc`、`grep`），不引入 npm/pip 依赖。

```bash
#!/usr/bin/env bash
set -e
SKILL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ERRORS=0

check() {
  if [ "$1" = "ok" ]; then
    echo "  ✓ $2"
  else
    echo "  ✗ $2"
    ERRORS=$((ERRORS + 1))
  fi
}

echo "Validating skill at $SKILL_ROOT"

# 1. manifest.json
[ -f "$SKILL_ROOT/manifest.json" ] && check ok "manifest.json exists" || check fail "manifest.json missing"
NAME=$(jq -r .name "$SKILL_ROOT/manifest.json" 2>/dev/null || echo "")
[ "$NAME" = "video-maker" ] && check ok "manifest.name == video-maker" || check fail "manifest.name mismatch: $NAME"
# ... version / category / description / compat

# 2. SKILL.md frontmatter
head -1 "$SKILL_ROOT/SKILL.md" | grep -q "^---$" && check ok "SKILL.md frontmatter" || check fail "SKILL.md frontmatter missing"
grep -q "^name: video-maker$" "$SKILL_ROOT/SKILL.md" && check ok "SKILL.md name" || check fail "SKILL.md name"

# 3. references 6 份
for ref in SCRIPT-STYLE OUTLINE-FORMAT CHAPTER-CRAFT THEMES AUDIO RECORDING; do
  f="$SKILL_ROOT/references/$ref.md"
  if [ -f "$f" ] && [ $(wc -c < "$f") -ge 100 ]; then
    check ok "references/$ref.md (≥ 100 chars)"
  else
    check fail "references/$ref.md (missing or empty)"
  fi
done

# 4. themes 5 套
for theme in midnight-press newsroom bauhaus-bold terminal-green monochrome-print; do
  d="$SKILL_ROOT/themes/$theme"
  [ -f "$d/theme.json" ] && [ -f "$d/tokens.css" ] && check ok "themes/$theme/" || check fail "themes/$theme/ incomplete"
  THEME_ID=$(jq -r .id "$d/theme.json" 2>/dev/null || echo "")
  [ "$THEME_ID" = "$theme" ] && check ok "themes/$theme: id matches" || check fail "themes/$theme: id != $theme"
done

# 5. ratify checklists
for c in script outline project; do
  [ -f "$SKILL_ROOT/ratify/reviewer-$c-checklist.md" ] && check ok "ratify/reviewer-$c-checklist.md" || check fail "ratify/reviewer-$c-checklist.md"
done

# 6. agents/reviewer.md
[ -f "$SKILL_ROOT/agents/reviewer.md" ] && [ $(wc -c < "$SKILL_ROOT/agents/reviewer.md") -ge 50 ] && check ok "agents/reviewer.md" || check fail "agents/reviewer.md"

# 7. templates/ 完整性
for f in package.json vite.config.ts src/App.tsx src/registry/chapters.ts src/registry/types.ts \
         src/styles/base.css src/styles/tokens.css \
         src/chapters/01-example/Example.tsx src/chapters/01-example/Example.css src/chapters/01-example/narrations.ts; do
  [ -f "$SKILL_ROOT/templates/$f" ] && check ok "templates/$f" || check fail "templates/$f"
done

# 8. scripts/ 4 个
for s in scaffold.sh extract-narrations.ts synthesize-audio.sh record-with-playwright.ts; do
  [ -f "$SKILL_ROOT/scripts/$s" ] && check ok "scripts/$s" || check fail "scripts/$s"
done

# Summary
echo ""
if [ $ERRORS -eq 0 ]; then
  M=$(find "$SKILL_ROOT" -type f | wc -l)
  N=$(find "$SKILL_ROOT/themes" -mindepth 1 -maxdepth 1 -type d | wc -l)
  K=$(find "$SKILL_ROOT/references" -name "*.md" -type f | wc -l)
  echo "✓ skill validation passed ($M files / $N themes / $K references)"
  exit 0
else
  echo "✗ skill validation failed: $ERRORS error(s)"
  exit 1
fi
```

`pnpm skill:validate` 入口在项目根 `package.json`：

```json
"scripts": {
  "skill:validate": "bash skills/video-maker/scripts/validate-skill.sh"
}
```

---

## 9. 端到端 Demo 执行计划

### 9.1 Demo 前置条件

- 阶段 1 需求 0-15、17、18 全部完成
- mmx-cli 或 qwen3 至少一个可用
- Playwright 已安装

### 9.2 Demo 步骤

| 步 | 动作 | 产物 | 时长 |
|---|---|---|---|
| 1 | 选 1 篇 Anthropic 博客（`demos/anthropic-article-demo/article.md`） | article.md | 30 min |
| 2 | 在 `demos/anthropic-article-demo/` 跑 `/video-maker`，传入 `article.md` | 触发 SKILL.md 工作流 | 5 min |
| 3 | Phase 1：Producer 一次产出 `script.md` + `outline.md` | 两文件 | 20 min（含 Reviewer 跑） |
| 4 | Checkpoint Plan 5 选 1：选 `midnight-press` + dev_mode=A + 全 placeholder | 决策记录 | 5 min |
| 5 | Phase 2：脚手架 + 第 1 章实现 + Ch1 Baseline 验收 | `presentation/` 项目 | 60-90 min |
| 6 | 第 2-N 章逐章实现（dev_mode=A） | 完整 `chapters/` | 90-120 min |
| 7 | Reviewer @ project full 跑过 | `reviewer-project-run-1.json` | 10 min |
| 8 | Checkpoint Audio：选合成 | 决策记录 | 1 min |
| 9 | Phase 3：`extract-narrations` + `synthesize-audio` | `audio-segments.json` + `public/audio/` | 30 min |
| 10 | Phase 4：`record-with-playwright` | `final.mp4` | 10 min（含视频长度） |
| 11 | 写 `RUN-LOG.md` 复盘 | 文档 | 30 min |

总计约 5-7 小时（人 + 代理协作），单次跑完。

### 9.3 Demo 验收标志

`demos/anthropic-article-demo/` 目录下齐全：

- `article.md`、`script.md`、`outline.md`
- `presentation/` 完整可跑
- `presentation/public/audio/` 各章音频齐全
- `final.mp4`（≥ 60s，可在播放器正常播放）
- `RUN-LOG.md`
- 3 份 `reviewer-*-run-*.json` 报告

---

## 10. 风险矩阵 + 验收 checklist

| 风险 | 影响 | 缓解 | 验收 |
|---|---|---|---|
| 5 套主题美学合格度参差 | 用户选 demo 时挑不到合适的 | 每套主题 DNA 一句话锚点 + 在 demo 中用 1 套验证 | demo 中实际跑通选定主题 |
| `templates/` 模板代码本身有 bug | 脚手架后用户跑不起来 | `validate-skill.sh` + demo 端到端验证 | demo Phase 2 能 `npm run dev` 起来 |
| Playwright 录屏首帧黑屏 | 录出来的视频开头有 200ms 黑屏 | ffmpeg `-ss 0.2` 裁掉 | demo `final.mp4` 第 1 帧已有内容 |
| mmx 与 qwen3 接入接口差异 | 切换 TTS 时脚本失败 | 统一最小契约 + `synthesize-audio.sh` 抽象层 | demo 测试两种 TTS 至少一种 |
| 主题切换后某章节代码硬编码颜色露馅 | 换主题视觉破 | CHAPTER-CRAFT.md Part 6 + Reviewer project 清单 | demo 中切换主题验证 1 章 |
| 旧 `skills/video-maker-v2/` 与新 skill 触发歧义 | 代理调用错 skill | manifest description 精确化 + 旧 skill 标 `[DEPRECATED]` | 新建会话输入"做视频"命中新 skill |
| Anthropic 博客内容版权 | 商用风险 | 限定 fair use + commit 中明确 + 不商用分发 demo MP4 | demo 仅作 portfolio，不分发 |
| `validate-skill.sh` 在 Windows 上跑不通 | 维护门槛高 | 用 git bash / WSL；阶段 2 加 PowerShell 等价 | Windows + git bash 跑通 |

---

## 11. 与 skills/video-maker-v2/ 共存隔离策略

### 11.1 命名空间隔离

| 维度 | video-maker-v2（旧） | video-maker（新） |
|---|---|---|
| Skill 名 | `video-maker-v2` | `video-maker` |
| Slash command | `/video-maker-v2` | `/video-maker` |
| manifest description | `[DEPRECATED] ...` | `...` |
| `.deepagents/skills/` 子目录 | `video-maker-v2-scriptwriter` / `video-maker-v2-remotion-builder`（保留供阶段 2 处理） | 阶段 1 不创建（DeepAgents 集成才需要） |

### 11.2 代理触发歧义缓解

旧 skill 的 frontmatter description 在阶段 1 完成时改为：

```yaml
---
name: video-maker-v2
description: "[DEPRECATED] Remotion 路线视频制作；已被 skills/video-maker/ (Web 录屏路线) 替代。除非显式要求 Remotion 输出，请使用 video-maker。"
---
```

代理在用户输入"做视频"时会优先匹配新 skill 的 description。

### 11.3 测试守护

阶段 1 不动 `tests/deepagents_video_maker/`：

- 现有测试断言 `skills/video-maker-v2/` 存在 → 仍通过（旧 skill 还在）
- 现有测试断言 `skills/video-maker-v2/agents/scriptwriter.md` 存在 → 仍通过
- 新增的 `validate-skill.sh` 在 `pnpm skill:validate` 触发，不在 `pytest` 路径

需求 0 移除 better-harness 后唯一改动的测试是 `test_skill_files.py` 的一个断言，不影响 v2 路径。

---

## 12. 阶段 1 实施顺序（→ tasks.md 草稿）

为了保证每一步都有"sanity check 验收"，建议实施顺序：

```
T0: 仓库清理（需求 0 + 17）
   ├─ 删 harness/ + runs/ + scripts/run-harness.ps1
   ├─ 删 package.json 中 harness:* scripts
   ├─ 改 CLAUDE.md
   ├─ 替换 test_skill_files 的断言
   ├─ skills/video-maker-v2/ 标 deprecated
   └─ commit: "chore: remove better-harness + mark video-maker-v2 deprecated"

T1: skill 骨架 + manifest 校验脚本（需求 1 + 18）
   ├─ 建 skills/video-maker/ 目录树（空文件占位）
   ├─ 写 SKILL.md 骨架（先空 4 Phase 标题）
   ├─ 写 manifest.json
   ├─ 写 README.md / README.zh-CN.md
   ├─ 写 validate-skill.sh
   ├─ 加 pnpm skill:validate
   └─ commit: "feat(skill): scaffold video-maker skill skeleton + validation script"

T2: 6 份 references（需求 2-7）
   ├─ SCRIPT-STYLE.md
   ├─ OUTLINE-FORMAT.md
   ├─ CHAPTER-CRAFT.md
   ├─ THEMES.md
   ├─ AUDIO.md
   ├─ RECORDING.md
   └─ commit each

T3: 5 套主题资产（需求 5）
   ├─ midnight-press
   ├─ newsroom
   ├─ bauhaus-bold
   ├─ terminal-green
   ├─ monochrome-print
   └─ commit: "feat(skill): add 5 built-in themes"

T4: Reviewer + 3 份 ratify checklist（需求 14）
   └─ commit: "feat(skill): add reviewer agent and 3 checklists"

T5: Vite 项目模板（需求 8 + 10）
   ├─ package.json / vite.config.ts / tsconfig.json
   ├─ src/styles/* / src/registry/*
   ├─ src/hooks/* / src/components/* / src/primitives/*
   ├─ src/App.tsx / src/main.tsx
   ├─ src/chapters/01-example/*
   └─ commit: "feat(skill): add Vite + React project template"

T6: scripts/（需求 9 + 6 + 7 + 15）
   ├─ scaffold.sh
   ├─ extract-narrations.ts
   ├─ synthesize-audio.sh
   ├─ record-with-playwright.ts
   └─ commit each

T7: 端到端 demo（需求 16）
   └─ commit: "demo: anthropic article end-to-end run"

T8: 阶段 1 验收 + PR
   └─ pnpm skill:validate 通过 + demo MP4 可播
```

每个 T 节点结束跑 `pnpm skill:validate`（除 T0），通过后才进下一节点。

---

## 13. 与阶段 2 的接口承诺

阶段 2 会做：

- `vm_*` LangChain tools 包装新 skill
- `state.yaml` / `goal.yaml` Python 解析器（如需要）
- 现有 Remotion 相关 langchain_tools 删除
- `tests/deepagents_video_maker/` 全面改造
- `skills/video-maker-v2/` 实际删除
- `.deepagents/skills/` 重组

阶段 1 给阶段 2 的承诺：

1. `skills/video-maker/` 目录结构稳定，阶段 2 可直接基于其调度
2. `validate-skill.sh` 输出格式稳定（阶段 2 的 CI 可消费）
3. demo 跑出来的 `presentation/` 目录结构作为阶段 2 LangChain tools 的"目标产物"参考
4. `narrations.ts` 真相源契约不变（阶段 2 的 `vm_extract_narrations` 等工具消费同一格式）
5. `record-with-playwright.ts` 可被阶段 2 直接 `subprocess` 调用，不需要重写

---

## 14. 待最终确认

5 项待确认问题已全部答完并落入设计：

| Q | 落点 |
|---|---|
| Q1 demo 文章 | §9.2 步骤 1（实施时挑） |
| Q2 templates 形式 | §1（直接拷贝目录） |
| Q3 Playwright 版本 | §5.1（latest stable，写到 templates/package.json） |
| Q4 mood 时长建议表 | §2 表格（非强制） |
| Q5 manifest 校验脚本 | §8 完整实现 + 需求 18 |

如需调整任一项请在确认 design.md 时一并指出。
