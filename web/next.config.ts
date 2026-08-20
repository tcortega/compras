import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  ...(process.env.SKIP_STATIC_PARAMS === '1' ? { output: 'standalone' as const } : {}),
  poweredByHeader: false,
  reactStrictMode: true,
  typedRoutes: true,
  allowedDevOrigins: ['127.0.0.1'],
}

export default nextConfig
