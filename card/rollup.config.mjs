import { nodeResolve } from '@rollup/plugin-node-resolve';
import terser from '@rollup/plugin-terser';
import typescript from '@rollup/plugin-typescript';

export default {
  input: 'src/brother-scanner-card.ts',
  output: {
    file: 'dist/brother-scanner-card.js',
    format: 'es',
    sourcemap: false,
  },
  plugins: [nodeResolve(), typescript({ tsconfig: './tsconfig.json' }), terser({ format: { comments: false } })],
};
