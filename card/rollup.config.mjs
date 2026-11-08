import { readFileSync } from 'node:fs';
import { nodeResolve } from '@rollup/plugin-node-resolve';
import terser from '@rollup/plugin-terser';
import typescript from '@rollup/plugin-typescript';

// The card is part of the integration: it is built into the integration's
// www/ folder, which the integration serves and registers as a dashboard
// resource, and it carries the integration's version from manifest.json.
const manifest = JSON.parse(readFileSync('../custom_components/brother_scanner/manifest.json', 'utf8'));

const version = {
  name: 'card-version',
  transform(code, id) {
    return id.endsWith('brother-scanner-card.ts') ? code.replace('__CARD_VERSION__', manifest.version) : null;
  },
};

export default {
  input: 'src/brother-scanner-card.ts',
  output: {
    file: '../custom_components/brother_scanner/www/brother-scanner-card.js',
    format: 'es',
    sourcemap: false,
  },
  plugins: [version, nodeResolve(), typescript({ tsconfig: './tsconfig.json' }), terser({ format: { comments: false } })],
};
