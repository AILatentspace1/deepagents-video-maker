#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const skillRoot = path.resolve(__dirname, '..');

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (!arg.startsWith('--')) continue;
    const key = arg.slice(2);
    const next = argv[i + 1];
    if (!next || next.startsWith('--')) args[key] = true;
    else {
      args[key] = next;
      i += 1;
    }
  }
  return args;
}

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function copyFile(src, dest) {
  ensureDir(path.dirname(dest));
  fs.copyFileSync(src, dest);
}

function normalizeAssetPath(p) {
  return p.replace(/\\/g, '/').replace(/^public\//, '');
}

function js(value) {
  return JSON.stringify(value, null, 2);
}

function validateLayouts(layouts, assetsById) {
  if (layouts.version !== 1) throw new Error('scene-layouts.version must be 1');
  if (!layouts.video || !Number.isFinite(layouts.video.width) || !Number.isFinite(layouts.video.height)) {
    throw new Error('scene-layouts.video.width/height are required numbers');
  }
  if (!Array.isArray(layouts.scenes) || layouts.scenes.length === 0) {
    throw new Error('scene-layouts.scenes must be a non-empty array');
  }
  const ids = new Set();
  for (const scene of layouts.scenes) {
    if (!scene.id || ids.has(scene.id)) throw new Error(`invalid or duplicate scene id: ${scene.id}`);
    ids.add(scene.id);
    if (!Number.isFinite(scene.durationSec) || scene.durationSec <= 0) throw new Error(`${scene.id}: durationSec must be > 0`);
    if (!scene.layout?.safeArea || !Array.isArray(scene.layout.regions)) throw new Error(`${scene.id}: layout.safeArea and regions are required`);
    for (const key of ['x', 'y', 'width', 'height']) {
      if (!Number.isFinite(scene.layout.safeArea[key])) throw new Error(`${scene.id}: safeArea.${key} must be a number`);
    }
    for (const region of scene.layout.regions) {
      for (const key of ['x', 'y', 'width', 'height']) {
        if (!Number.isFinite(region[key])) throw new Error(`${scene.id}/${region.id}: region.${key} must be a number`);
      }
      if (region.x < 0 || region.y < 0 || region.x + region.width > layouts.video.width || region.y + region.height > layouts.video.height) {
        throw new Error(`${scene.id}/${region.id}: region exceeds canvas bounds`);
      }
    }
    for (const assetRef of scene.assetRefs ?? []) {
      if (!assetsById.has(assetRef)) throw new Error(`${scene.id}: missing assetRef ${assetRef}`);
    }
  }
}

function writeProjectFiles(outDir, layouts, manifest, copiedAssets) {
  ensureDir(path.join(outDir, 'src'));
  ensureDir(path.join(outDir, 'public', 'assets'));
  ensureDir(path.join(outDir, 'out'));

  const props = {
    video: layouts.video,
    scenes: layouts.scenes,
    assets: Object.fromEntries(copiedAssets.map((a) => [a.id, { ...a, publicPath: `assets/${path.basename(a.path)}` }])),
  };
  fs.writeFileSync(path.join(outDir, 'props.json'), js(props), 'utf8');

  fs.writeFileSync(path.join(outDir, 'package.json'), js({
    name: 'layout-first-remotion-smoke',
    version: '0.0.0',
    private: true,
    type: 'module',
    scripts: {
      render: 'remotion render src/index.ts LayoutVideo --props=props.json --output=out/video.mp4 --gl=angle --concurrency=50%',
      studio: 'remotion studio src/index.ts',
      typecheck: 'tsc --noEmit',
    },
    dependencies: {
      '@remotion/cli': '4.0.438',
      '@remotion/zod-types': '4.0.438',
      react: '19.2.0',
      'react-dom': '19.2.0',
      remotion: '4.0.438',
      typescript: '5.9.3',
      zod: '4.3.6',
    },
    devDependencies: {
      '@types/react': '19.2.14',
      '@types/react-dom': '19.2.3',
    },
  }), 'utf8');

  fs.writeFileSync(path.join(outDir, 'tsconfig.json'), js({
    compilerOptions: {
      target: 'ES2022',
      module: 'ESNext',
      moduleResolution: 'bundler',
      jsx: 'react-jsx',
      strict: true,
      esModuleInterop: true,
      skipLibCheck: true,
      noEmit: true,
      types: ['node'],
    },
    include: ['src/**/*'],
  }), 'utf8');

  fs.writeFileSync(path.join(outDir, 'src', 'index.ts'), `import { registerRoot } from 'remotion';\nimport { RemotionRoot } from './Root';\n\nregisterRoot(RemotionRoot);\n`, 'utf8');

  fs.writeFileSync(path.join(outDir, 'src', 'schema.ts'), `import { z } from 'zod';\n\nconst RegionSchema = z.object({\n  id: z.string(),\n  role: z.string(),\n  x: z.number(),\n  y: z.number(),\n  width: z.number(),\n  height: z.number(),\n});\n\nconst SceneSchema = z.object({\n  id: z.string(),\n  durationSec: z.number().positive(),\n  intent: z.string(),\n  layout: z.object({\n    type: z.string(),\n    safeArea: z.object({ x: z.number(), y: z.number(), width: z.number(), height: z.number() }),\n    regions: z.array(RegionSchema),\n  }),\n  content: z.record(z.string(), z.unknown()).default({}),\n  motion: z.record(z.string(), z.unknown()).optional(),\n  assetRefs: z.array(z.string()).default([]),\n});\n\nexport const LayoutVideoSchema = z.object({\n  video: z.object({\n    title: z.string(),\n    width: z.number().int().positive(),\n    height: z.number().int().positive(),\n    fps: z.number().int().positive(),\n    style: z.string().optional(),\n    background: z.string().optional(),\n  }),\n  scenes: z.array(SceneSchema),\n  assets: z.record(z.string(), z.object({\n    id: z.string(),\n    type: z.string(),\n    path: z.string(),\n    description: z.string(),\n    recommendedUse: z.string().optional(),\n    publicPath: z.string(),\n  })),\n});\n\nexport type LayoutVideoProps = z.infer<typeof LayoutVideoSchema>;\nexport type LayoutScene = LayoutVideoProps['scenes'][number];\n`, 'utf8');

  fs.writeFileSync(path.join(outDir, 'src', 'Root.tsx'), `import React from 'react';\nimport { Composition } from 'remotion';\nimport type { CalculateMetadataFunction } from 'remotion';\nimport { LayoutVideo } from './Video';\nimport { LayoutVideoSchema, type LayoutVideoProps } from './schema';\nimport defaultProps from '../props.json';\n\nconst calculateMetadata: CalculateMetadataFunction<LayoutVideoProps> = async ({ props }) => {\n  const durationInFrames = props.scenes.reduce((sum, scene) => sum + Math.ceil(scene.durationSec * props.video.fps), 0);\n  return {\n    width: props.video.width,\n    height: props.video.height,\n    fps: props.video.fps,\n    durationInFrames,\n  };\n};\n\nexport const RemotionRoot: React.FC = () => (\n  <Composition\n    id=\"LayoutVideo\"\n    component={LayoutVideo}\n    width={defaultProps.video.width}\n    height={defaultProps.video.height}\n    fps={defaultProps.video.fps}\n    durationInFrames={defaultProps.scenes.reduce((sum, scene) => sum + Math.ceil(scene.durationSec * defaultProps.video.fps), 0)}\n    defaultProps={defaultProps as LayoutVideoProps}\n    schema={LayoutVideoSchema}\n    calculateMetadata={calculateMetadata}\n  />\n);\n`, 'utf8');

  fs.writeFileSync(path.join(outDir, 'src', 'Video.tsx'), `import React from 'react';\nimport { AbsoluteFill, Img, Series, staticFile, interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';\nimport type { LayoutScene, LayoutVideoProps } from './schema';\n\nconst palette = {\n  text: '#f8fafc',\n  muted: '#cbd5e1',\n  panel: 'rgba(15, 23, 42, 0.72)',\n  panelStrong: 'rgba(30, 41, 59, 0.86)',\n  border: 'rgba(148, 163, 184, 0.28)',\n  accent: '#67e8f9',\n};\n\nfunction Region({ region, children, style = {} }: { region: LayoutScene['layout']['regions'][number]; children: React.ReactNode; style?: React.CSSProperties }) {\n  return (\n    <div style={{ position: 'absolute', left: region.x, top: region.y, width: region.width, height: region.height, ...style }}>\n      {children}\n    </div>\n  );\n}\n\nfunction FitText({ children, size = 28, muted = false }: { children: React.ReactNode; size?: number; muted?: boolean }) {\n  return <div style={{ color: muted ? palette.muted : palette.text, fontSize: size, lineHeight: 1.16, fontWeight: muted ? 500 : 800 }}>{children}</div>;\n}\n\nfunction useEntrance(delay = 0) {\n  const frame = useCurrentFrame();\n  const { fps } = useVideoConfig();\n  const progress = spring({ frame: frame - delay, fps, config: { damping: 200 }, durationInFrames: Math.round(0.65 * fps) });\n  return {\n    opacity: interpolate(progress, [0, 1], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),\n    transform: 'translateY(' + interpolate(progress, [0, 1], [24, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) + 'px) scale(' + interpolate(progress, [0, 1], [0.98, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) + ')',\n  } satisfies React.CSSProperties;\n}\n\nfunction AssetImage({ assetPath, mode = 'contain' }: { assetPath: string; mode?: 'contain' | 'cover' }) {\n  return <Img src={staticFile(assetPath)} style={{ width: '100%', height: '100%', objectFit: mode, borderRadius: 18 }} />;\n}\n\nfunction SceneView({ scene, assets, background }: { scene: LayoutScene; assets: LayoutVideoProps['assets']; background?: string }) {\n  const titleStyle = useEntrance(2);\n  const bodyStyle = useEntrance(10);\n  const firstAsset = scene.assetRefs[0] ? assets[scene.assetRefs[0]] : undefined;\n  const byId = Object.fromEntries(scene.layout.regions.map((r) => [r.id, r]));\n\n  return (\n    <AbsoluteFill style={{ background: background ?? '#020617', fontFamily: 'Inter, Arial, sans-serif', overflow: 'hidden' }}>\n      <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(135deg, rgba(103,232,249,0.16), transparent 35%, rgba(99,102,241,0.16))' }} />\n      {scene.layout.type === 'hero_title' && (\n        <>\n          <Region region={byId.title} style={{ ...titleStyle, display: 'flex', alignItems: 'end', justifyContent: 'center', textAlign: 'center' }}>\n            <FitText size={44}>{String(scene.content.title ?? '')}</FitText>\n          </Region>\n          <Region region={byId.subtitle} style={{ ...bodyStyle, display: 'flex', alignItems: 'start', justifyContent: 'center', textAlign: 'center' }}>\n            <FitText size={22} muted>{String(scene.content.subtitle ?? '')}</FitText>\n          </Region>\n        </>\n      )}\n      {scene.layout.type === 'image_left_text_right' && firstAsset && (\n        <>\n          <Region region={byId.visual} style={{ ...titleStyle, padding: 6, background: palette.panel, border: '1px solid ' + palette.border, borderRadius: 22 }}>\n            <AssetImage assetPath={firstAsset.publicPath} />\n          </Region>\n          <Region region={byId.body} style={{ ...bodyStyle, display: 'flex', flexDirection: 'column', gap: 12, justifyContent: 'center' }}>\n            <FitText size={26}>{String(scene.content.title ?? '')}</FitText>\n            {(Array.isArray(scene.content.bullets) ? scene.content.bullets : []).map((item, index) => (\n              <div key={String(item)} style={{ color: palette.muted, fontSize: 18, padding: '8px 12px', borderRadius: 999, background: palette.panelStrong, border: '1px solid ' + palette.border, opacity: useEntrance(16 + index * 6).opacity }}>\n                {String(item)}\n              </div>\n            ))}\n          </Region>\n        </>\n      )}\n      {scene.layout.type === 'full_bleed_asset_with_caption' && firstAsset && (\n        <>\n          <Region region={byId.background} style={{ ...titleStyle, padding: 4, background: palette.panel, borderRadius: 22 }}>\n            <AssetImage assetPath={firstAsset.publicPath} mode=\"cover\" />\n          </Region>\n          <Region region={byId.caption} style={{ ...bodyStyle, display: 'flex', alignItems: 'center', justifyContent: 'center', textAlign: 'center', background: palette.panelStrong, border: '1px solid ' + palette.border, borderRadius: 999 }}>\n            <FitText size={18}>{String(scene.content.caption ?? '')}</FitText>\n          </Region>\n        </>\n      )}\n      <div style={{ position: 'absolute', right: 20, bottom: 16, color: palette.accent, fontSize: 12, letterSpacing: 1.5, opacity: 0.75 }}>{scene.id} / {scene.intent}</div>\n    </AbsoluteFill>\n  );\n}\n\nexport const LayoutVideo: React.FC<LayoutVideoProps> = ({ video, scenes, assets }) => {\n  return (\n    <Series>\n      {scenes.map((scene) => (\n        <Series.Sequence key={scene.id} durationInFrames={Math.ceil(scene.durationSec * video.fps)}>\n          <SceneView scene={scene} assets={assets} background={video.background} />\n        </Series.Sequence>\n      ))}\n    </Series>\n  );\n};\n`, 'utf8');
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const fixtureDir = path.resolve(args.fixture ?? path.join(skillRoot, 'fixtures', 'layout-builder'));
  const layoutsPath = path.resolve(args.layouts ?? path.join(fixtureDir, 'scene-layouts.json'));
  const manifestPath = path.resolve(args.assets ?? path.join(fixtureDir, 'asset-manifest.json'));
  const outDir = path.resolve(args.out ?? path.join(process.cwd(), 'output', 'layout-builder-smoke', 'remotion-project'));
  const nodeModulesFrom = args['link-node-modules'] ? path.resolve(String(args['link-node-modules'])) : undefined;

  const layouts = readJson(layoutsPath);
  const manifest = readJson(manifestPath);
  const manifestBase = path.dirname(manifestPath);
  const assetDir = path.resolve(manifestBase, manifest.assetDir ?? '.');
  const assetsById = new Map((manifest.assets ?? []).map((a) => [a.id, a]));
  validateLayouts(layouts, assetsById);

  fs.rmSync(outDir, { recursive: true, force: true });
  ensureDir(outDir);

  const copiedAssets = [];
  for (const asset of manifest.assets ?? []) {
    const src = path.resolve(assetDir, asset.path);
    if (!fs.existsSync(src)) throw new Error(`asset not found: ${src}`);
    const dest = path.join(outDir, 'public', 'assets', path.basename(asset.path));
    copyFile(src, dest);
    copiedAssets.push({ ...asset, path: normalizeAssetPath(asset.path) });
  }

  writeProjectFiles(outDir, layouts, manifest, copiedAssets);

  if (nodeModulesFrom) {
    const target = path.join(outDir, 'node_modules');
    if (!fs.existsSync(target)) {
      fs.symlinkSync(nodeModulesFrom, target, 'junction');
    }
  }

  const report = {
    outDir,
    scenes: layouts.scenes.length,
    assets: copiedAssets.length,
    renderCommand: 'pnpm exec remotion render src/index.ts LayoutVideo --props=props.json --output=out/video.mp4 --gl=angle --concurrency=50%',
  };
  fs.writeFileSync(path.join(outDir, 'builder-report.json'), js(report), 'utf8');
  console.log(JSON.stringify(report, null, 2));
}

main();
