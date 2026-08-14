import coreWebVitals from "eslint-config-next/core-web-vitals";
import typescript from "eslint-config-next/typescript";

// eslint-config-next ships native flat configs, so no FlatCompat wrapper is
// needed - and with ESLint 10 the wrapper throws on this config.
const config = [
  { ignores: [".next/**", "node_modules/**", "next-env.d.ts"] },
  ...coreWebVitals,
  ...typescript,
];

export default config;
