import { dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Explicit root avoids Next.js selecting parent workspace because of multiple lockfiles.
  turbopack: {
    root: __dirname,
  },
  webpack(config, { dev }) {
    // Workaround for intermittent dev bundler corruption (missing .next server/client chunks)
    // by disabling webpack persistent cache in development.
    if (dev) {
      config.cache = false;
    }
    return config;
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:4000/api/:path*',
      },
    ];
  },
};

export default nextConfig;
