/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    // Evita spawn de worker no build em ambientes Windows restritos
    // (erro recorrente: Error: spawn EPERM).
    webpackBuildWorker: false,
    workerThreads: false,
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
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'www.brigadamilitar.rs.gov.br',
      },
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8000',
      },
    ],
  },
  env: {
    API_URL: process.env.API_URL || 'http://localhost:8000',
  },
  webpack: (config, { isServer }) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      'mapbox-gl': 'maplibre-gl',
    };
    
    // Fix for DataCloneError in worker threads
    if (!isServer) {
      config.optimization = {
        ...config.optimization,
        splitChunks: {
          ...config.optimization.splitChunks,
          chunks: 'all',
        },
      };
    }
    
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
