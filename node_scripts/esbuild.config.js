const esbuild = require('esbuild');

esbuild.build({
  entryPoints: ['index.js'],
  bundle: true,
  platform: 'node',
  target: 'node18',
  outfile: '../build/node-sharp-fixed/bundle.js',
  external: ['sharp'], // Keep sharp as external
  minify: true,
  sourcemap: false,
  format: 'cjs',
  banner: {
    js: '#!/usr/bin/env node'
  }
}).catch(() => process.exit(1));
