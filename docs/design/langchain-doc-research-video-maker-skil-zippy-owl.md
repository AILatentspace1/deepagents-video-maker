# Plan: deepagent-video-maker-ui 全栈式 UI 优化

## Context

`E:\workspace\orchestrator_skills\deepagent-video-maker-ui` 是 langchain-ai/deep-agents-ui 的 fork，承担 video-maker DeepAgent (LangGraph) 的前端。当前 UI 是通用的 chat shell，但 video-maker 这个 producer workflow 的实际场景有几个特殊需求未被满足：

- 工作流分 4 个里程碑（research → script → assets → assembly），每个里程碑 5–30 分钟，需要可见的进度反馈
- 大量 subagent 派发链（researcher / scriptwriter / scene-batch-generator / evaluator 等），用户需要看清父子关系
- 关键产物是多媒体（mp4 视频 / png 图片 / json manifest），目前 FileViewDialog 只能预览文本/markdown
- assets 里程碑有 manual audio pause 中断，审批 UI 仍是 raw JSON 编辑

通用的 UI 问题：硬编码颜色（`#2F6868`、`#3F3F46`、`#70707B`）破坏深青色主题 token 体系；多处 dark mode 缺补丁（`STATUS_COLORS` 用 `bg-green-500` 而非 CSS 变量）；`focus-visible:ring-0` 移除了焦点环影响键盘可达性；消息流无虚拟化在长 thread 下卡顿。

用户决策：**全栈式优化** + **硬 fork（不再考虑 upstream merge）** + **必须支持 mp4/png/jpg 预览**。

---

## 实施分期

按 PR 大小切分为 5 个 phase，每个 phase 独立可 ship 并通过 `pnpm dev` 验证。建议每个 phase 一个 PR，便于 review。

---

### Phase A — Foundation polish（设计 token + dark mode + a11y）

**目标：** 修掉所有硬编码视觉值、补全 dark mode、恢复焦点环。无新增功能，只是清理。

**关键改动：**

1. **Token 化品牌色** — `src/app/globals.css`
   - 新增语义 token：`--brand-accent`（替代 `#2F6868`）、`--badge-count-bg`、`--subagent-name`、`--subagent-chevron`，light/dark 各定义一份
   - 把 `STATUS_COLORS` 也搬到 CSS 变量：`--status-idle / --status-busy / --status-interrupted / --status-error`，并在 dark 模式下使用降饱和度变体

2. **替换硬编码颜色**
   - `src/app/components/ChatInterface.tsx:441,487` — `bg-[#2F6868]` → `bg-[hsl(var(--brand-accent))]`
   - `src/app/components/SubAgentIndicator.tsx:26,33` — `text-[#3F3F46]` / `text-[#70707B]` → `text-foreground` / `text-muted-foreground`
   - `src/app/components/ThreadList.tsx:34-39` — `STATUS_COLORS` 改读 CSS 变量
   - `src/app/components/ToolApprovalInterrupt.tsx:270,272` — 把 `dark:bg-green-600` 等独立 dark 写法整合进语义 token
   - `src/app/page.tsx:159` — `border-[#2F6868] bg-[#2F6868]` → 用 `--brand-accent`

3. **恢复焦点环**
   - `src/app/components/ToolCallBox.tsx:117` 等所有出现 `focus-visible:ring-0 focus-visible:ring-offset-0` 的位置 — 改回 `focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2`
   - `globals.css:14-16` 已有 `outline-color: hsl(var(--primary))` 全局规则，保留并验证不被覆盖

4. **ARIA / 语义化补齐**
   - `ChatInterface.tsx:365-424` task summary 按钮 — 新增 `aria-label="View milestone tasks"` / `aria-label="View output files"`
   - `ThreadList.tsx:329-336` status 圆点 — 包一层 `<span role="status" aria-label={`Status: ${status}`}>`
   - `SubAgentIndicator.tsx` Button — `aria-expanded={isExpanded}` + `aria-controls`

5. **可读性补丁**
   - `ChatMessage.tsx:111` user message 在 dark 下 `--color-user-message-bg: #2d2d2d` 但 `text-foreground` 对比度足够，验证后保留；如不达标则在 dark 下改用 `bg-secondary`
   - 字号统一：去掉 `text-[10px]`、`text-[15px]` 等异类，统一到 tailwind scale `xxs/xs/sm/base`（已在 `tailwind.config.mjs` 定义）

**修改文件：** `globals.css`, `tailwind.config.mjs`(可选), `ChatInterface.tsx`, `SubAgentIndicator.tsx`, `ThreadList.tsx`, `ToolApprovalInterrupt.tsx`, `ToolCallBox.tsx`, `page.tsx`, `ChatMessage.tsx`

---

### Phase B — Video-Maker Workflow 可视化（milestone + subagent 派发树）

**目标：** 让用户一眼看出 video-maker 处于哪个 milestone、哪些 subagent 在跑、它们之间什么关系。这是这次优化的最大价值点。

**新增组件：**

1. **`src/app/components/MilestonePipeline.tsx`** — 顶部水平进度条
   - 4 个 step：Research / Script / Assets / Assembly
   - 每个 step 三态：pending（灰）/ running（深青脉冲）/ completed（绿√）
   - 视觉：水平 stepper，连接线 + 圆形 step + 标签 + 百分比 hint
   - 数据源：解析 `todos[]` 中的 `content` 文本（约定关键词如 "research"/"script"/"assets"/"assembly"），或解析 `files[]` 出现哪个产物（`research.md` 完成 → research done；`manifest.json` → assets done；`video.mp4` → assembly done）
   - 推荐放在 `page.tsx` header 下方、`ResizablePanelGroup` 上方，全宽显示

2. **`src/app/lib/milestones.ts`** — milestone 推导逻辑
   - `inferMilestoneFromTodos(todos): Record<MilestoneKey, status>`
   - `inferMilestoneFromFiles(files): Record<MilestoneKey, status>`
   - 合并两者 → 返回 `{milestone, label, status, percent, activeStep}`
   - 单元可测，不依赖 React

3. **`src/app/components/SubAgentTree.tsx`** — 替换 `ChatMessage.tsx:150-193` 的扁平 subagent 列表
   - 解析 message 间的派发关系（parent ai message → task tool_call → child subagent → 它产生的下层 task tool_call）
   - 用 indentation + 连接线（`border-l-2 border-border`）渲染父子层级
   - 每个节点显示：`subAgentName`（researcher / scriptwriter / scene-batch-generator）+ status（running spinner / completed √ / failed ⚠）+ 输入/输出折叠按钮
   - 保留现有"展开看 input/output"行为，但持久化到 localStorage（key `subagent-expanded-${threadId}`），避免切换 thread 重置

4. **Task 按 milestone 分组** — `src/app/components/ChatInterface.tsx:341-546`
   - 当前按 `pending/in_progress/completed` status 分组；改为先按 milestone 分组、再按 status 分组（或加个 toggle）
   - 每个 milestone 子组显示 `Tasks 3/8 done`
   - milestone 推导用 Phase B 的 `lib/milestones.ts`

**修改文件：** 新增 3 个组件 + `lib/milestones.ts`；改 `ChatInterface.tsx`, `ChatMessage.tsx`, `page.tsx`

---

### Phase C — 媒体预览 & 文件–milestone 关联（用户明确要求）

**目标：** 让 mp4 / png / jpg 在 UI 中可直接预览；让 Files 列表按 milestone 分组，每个文件标注归属。

**关键改动：**

1. **扩展 `src/app/components/FileViewDialog.tsx`**
   - 新增 `getMediaType(filename): "video" | "image" | "audio" | "text"`
   - `.mp4 / .webm / .mov` → `<video controls preload="metadata" />` + 下载按钮
   - `.png / .jpg / .jpeg / .webp / .gif` → `<img alt={filename} />` + 缩放/下载
   - `.mp3 / .wav` → `<audio controls />`
   - `.json` → 已有的 markdown render fallback，但用 syntax-highlighter 高亮
   - 数据来源：`files[filename]` 当前是字符串内容；如果是 base64 / data-url，构造 blob URL；如果是文件路径（虚拟路径），构造 `/api/files?path=...` 的 GET 请求（需要 Next.js API route `src/app/api/files/route.ts` 或读 LangGraph state 同步返回）

2. **新增 `src/app/api/files/route.ts`**（仅当 LangGraph state 用虚拟路径时）
   - 接受 `?path=<virtual-path>` 查询，调 LangGraph SDK 拉取文件 raw bytes
   - 设置正确 `Content-Type` 头（mp4 / png 等）
   - 仅本地 dev 用，生产部署再加鉴权

3. **Files 按 milestone 分组** — `src/app/components/TasksFilesSidebar.tsx`
   - 新增 `inferFileMilestone(filename): MilestoneKey`（通过文件名前缀/后缀匹配：`research.md → research`，`script.md → script`，`manifest.json|*.png|*.mp3 → assets`，`*.mp4 → assembly`）
   - 网格按 milestone 分组渲染，每组带标题
   - 每个文件卡片右上角添加 milestone badge（小色块）

4. **缩略图预览** — `TasksFilesSidebar.tsx`
   - 文件卡片如果是图片，渲染 thumbnail（80×80 cover）
   - 视频则渲染第一帧（用 `<video>` 加 `preload="metadata"` + `currentTime=0.1`）
   - 文本/JSON 渲染前 3 行 preview

**修改文件：** `FileViewDialog.tsx`（重写一半）, `TasksFilesSidebar.tsx`, 新增 `lib/file-types.ts`, 可能新增 `app/api/files/route.ts`

---

### Phase D — 性能 & 可靠性

**目标：** 长 thread / 大量消息下不卡，自动滚动可控。

**关键改动：**

1. **消息列表虚拟化** — `ChatInterface.tsx:295-330`
   - 引入 `react-virtuoso`（package.json 加依赖）替代直接 `.map()`
   - 配置 `followOutput="smooth"` 让新消息自动滚到底部，但用户主动滚回上方时停止
   - `useStickToBottom` 与 virtuoso 互斥，移除 `useStickToBottom` 改用 virtuoso 内置行为

2. **Thread list 懒加载阈值优化** — `ThreadList.tsx`
   - 当前 `limit=20` 手动 Load More；改为 IntersectionObserver 自动预取下一页
   - 添加搜索框：title fuzzy match（用 lodash `debounce` 300ms）

3. **ResizablePanel resize 防抖** — `page.tsx`
   - resize 期间消息列表不重新计算高度（virtuoso 会自动处理）
   - 验证 ResizableHandle 可见性，避免 hover 才出现导致用户找不到

**新增依赖：** `react-virtuoso`（运行时）

**修改文件：** `ChatInterface.tsx`, `ThreadList.tsx`, `page.tsx`

---

### Phase E — 工具审批 & 配置 polish

**目标：** 让 manual audio pause 等中断的审批不再让用户改 raw JSON；让首次配置流畅。

**关键改动：**

1. **ToolApprovalInterrupt 表单化** — `src/app/components/ToolApprovalInterrupt.tsx`
   - 当前 args 是 textarea（line 135-176 附近）；改为根据 `actionRequest.args` 的字段类型推导：
     - `string` → `<Input />`
     - `boolean` → `<Switch />`
     - `number` → `<Input type="number" />`
     - `enum`（基于 `reviewConfig` 暗示）→ `<Select />`
   - 保留"Edit raw JSON"高级模式作为 escape hatch
   - 字段级别校验错误提示

2. **ConfigDialog 友好化** — `src/app/components/ConfigDialog.tsx`
   - 顶部加"Quick start"步骤提示（如何在仓库根 `pnpm agent:dev` 起 LangGraph dev）
   - 新增"Test connection"按钮：发起 `client.assistants.search({graphId, limit:1})` 验证连通性，显示绿/红 badge
   - Assistant ID 字段下方加"View available assistants"链接，点开下拉显示当前 graph 的 assistants
   - 用 `alert()`（line 50）改为 inline 错误消息

3. **空状态 / 长加载反馈** — 全局
   - `ChatInterface.tsx` 当 `isLoading=true` 且 message 增长慢时，每 30s 显示一次 heartbeat（"Researcher is working… 已耗时 1m 23s"）
   - `page.tsx:255` 欢迎屏增加示例 prompt 卡片（点击直接填入），降低首次使用门槛

**修改文件：** `ToolApprovalInterrupt.tsx`, `ConfigDialog.tsx`, `ChatInterface.tsx`, `page.tsx`

---

## 不在范围内（明确排除）

- 重写后端 LangGraph agent 逻辑（`agent/agent.py` 不动）
- 改 video-maker skill 本身（`.claude/skills/video-maker/` 不动）
- 改 LangGraph SDK 协议（`@langchain/langgraph-sdk` 用法不变）
- i18n / 多语言（保持英文 UI）
- 移动端响应式（聚焦桌面 desktop ≥ 1024px）

---

## Verification

每个 phase 完成后运行：

1. **静态检查**
   ```bash
   cd E:/workspace/orchestrator_skills/deepagent-video-maker-ui
   corepack yarn lint
   corepack yarn format:check
   ```

2. **构建验证**
   ```bash
   corepack yarn build
   ```

3. **E2E 跑通 video-maker 一次完整 session**（最关键）
   ```bash
   # 终端 1：起 LangGraph
   corepack yarn agent:dev
   # 终端 2：起 UI
   corepack yarn dev
   ```
   - 浏览器打开 `http://localhost:3000`
   - 用 README 里的示例 prompt 启动一个 video-maker session
   - 观察：milestone progress bar 是否随 research → script → assets → assembly 推进、subagent tree 是否正确展示父子关系、视频 mp4 在 FileViewDialog 是否能播、focus ring 在 Tab 键导航时可见、dark mode（系统级别切换）是否完整覆盖

4. **可访问性快速过**
   - Chrome DevTools → Lighthouse Accessibility 跑分（目标 ≥ 95）
   - 仅键盘操作完成"打开 thread → 发送消息 → 预览视频"全流程

5. **性能验证**
   - 用一个 200+ 消息的长 thread 滚动，FPS 监控不低于 50
   - Files 含 1 个 5MB mp4 + 10 个 png，FileViewDialog 切换不卡顿

---

## 关键文件清单

**Phase A 触及：**
- `src/app/globals.css`
- `src/app/page.tsx`
- `src/app/components/ChatInterface.tsx`
- `src/app/components/ChatMessage.tsx`
- `src/app/components/SubAgentIndicator.tsx`
- `src/app/components/ThreadList.tsx`
- `src/app/components/ToolApprovalInterrupt.tsx`
- `src/app/components/ToolCallBox.tsx`

**Phase B 触及（新增 + 改）：**
- 新 `src/app/components/MilestonePipeline.tsx`
- 新 `src/app/components/SubAgentTree.tsx`
- 新 `src/app/lib/milestones.ts`
- 改 `src/app/components/ChatInterface.tsx`, `ChatMessage.tsx`, `page.tsx`

**Phase C 触及：**
- `src/app/components/FileViewDialog.tsx`（半重写）
- `src/app/components/TasksFilesSidebar.tsx`
- 新 `src/app/lib/file-types.ts`
- 可能新 `src/app/api/files/route.ts`

**Phase D 触及：**
- `package.json`（加 `react-virtuoso`）
- `src/app/components/ChatInterface.tsx`
- `src/app/components/ThreadList.tsx`

**Phase E 触及：**
- `src/app/components/ToolApprovalInterrupt.tsx`
- `src/app/components/ConfigDialog.tsx`
- `src/app/components/ChatInterface.tsx`
- `src/app/page.tsx`

---

## 复用的现有工具与库

- shadcn 基础组件已具备：`Button / Dialog / Input / Switch / Select / Tabs / Tooltip / ScrollArea / Skeleton`
- `react-syntax-highlighter` 已在依赖中（用于 JSON / code preview）
- `react-markdown + remark-gfm` 已在用（保留）
- `lucide-react` 图标统一来源（避免 emoji icon）
- `date-fns` 用于时间格式化（已在 ThreadList 用）
- `clsx + tailwind-merge` 经 `cn()` 合并 className
- `nuqs` URL state（threadId / sidebar / 可加 milestone tab state）

---

## 估算与建议执行顺序

| Phase | 估算 PR 大小 | 风险 | 顺序 |
|---|---|---|---|
| A — Foundation | 中（10-15 文件小改） | 低 | 1️⃣ 先做，让后续基于干净 token |
| C — 媒体预览 | 中（3-4 文件 + 可能 1 API route） | 中（取决于 LangGraph state 文件传输方式） | 2️⃣ 用户重点诉求，先于 B 验证文件取得 |
| B — Workflow 可视化 | 大（3 新组件 + 改 3 文件） | 中（milestone 推导逻辑可能需要迭代） | 3️⃣ 价值最高但最复杂，放后面 |
| D — 性能 | 小-中（2-3 文件 + 1 依赖） | 低 | 4️⃣ 长 thread 出现后必要 |
| E — Polish | 小（4 文件小改） | 低 | 5️⃣ 收尾 |

每个 Phase 一个 worktree（`feat/ui-phase-a-tokens` 等），独立 PR 合 main。

---

## 待用户在执行阶段确认的小问题

这些不阻塞 plan 通过，等开工时再问：

1. LangGraph state 中 video-maker 输出文件是 base64 内联还是虚拟路径？这决定 Phase C 是否需要新增 `/api/files` route
2. milestone 名字最终对外用 "Research/Script/Assets/Assembly" 还是中文？（建议英文，与代码一致）
3. 是否要保留 ConfigDialog 的"首次进入自动弹出"行为，还是改为顶部 banner？
