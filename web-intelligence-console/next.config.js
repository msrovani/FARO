/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  experimental: {
    // Evita spawn de worker no build em ambientes Windows restritos
    // (erro recorrente: Error: spawn EPERM).
    webpackBuildWorker: false,
    workerThreads: true,
  },
  eslint: {
    // Lint e type-check rodam como gate separado no CI.
    ignoreDuringBuilds: true,
  },
  typescript: {
    // Evita etapa de type-check dentro do next build (tambem usa worker).
    ignoreBuildErrors: true,
  },
  images: {
    domains: ['localhost', 'www.brigadamilitar.rs.gov.br'],
  },
  env: {
    API_URL: process.env.API_URL || 'http://localhost:8000',
  },
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      'mapbox-gl': 'maplibre-gl',
    };
    return config;
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.API_URL || 'http://localhost:8000'}/api/v1/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
