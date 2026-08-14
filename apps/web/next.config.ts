import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Emits a self-contained server bundle, so the runtime image can copy just
  // that instead of the whole node_modules tree. See apps/web/Dockerfile.
  output: "standalone",

  // The API address is read at request time, not baked in at build time, so
  // one image runs in every environment.
  env: {},

  typedRoutes: true,
};

export default nextConfig;
