import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  turbopack: {
    // Set root to workspace root so Turbopack can follow pnpm symlinks
    // into node_modules/.pnpm which lives at workspace root, not web-ui/
    root: path.resolve(__dirname, ".."),
  },
};

export default nextConfig;
