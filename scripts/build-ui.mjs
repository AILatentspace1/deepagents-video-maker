import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const uiRoot = path.join(root, "web-ui");
const nextBin = path.join(uiRoot, "node_modules", "next", "dist", "bin", "next");

const env = {
  ...process.env,
  NEXT_TELEMETRY_DISABLED: process.env.NEXT_TELEMETRY_DISABLED || "1",
  CI: process.env.CI || "1",
};

if (process.platform === "win32" && existsSync("C:\\tmp")) {
  env.TEMP = process.env.TEMP || "C:\\tmp";
  env.TMP = process.env.TMP || "C:\\tmp";
}

const result = spawnSync(process.execPath, [nextBin, "build"], {
  cwd: uiRoot,
  env,
  stdio: "inherit",
  windowsHide: true,
});

process.exit(result.status ?? 1);
