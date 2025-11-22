/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  async rewrites() {
    // Get API base URL from environment variable (loaded from root .env)
    // Fallback to IPv4 for backward compatibility
    const apiBaseUrl = process.env.API_BASE_URL || 'http://127.0.0.1:8080';
    
    return [
      {
        source: '/api/:path*',
        destination: `${apiBaseUrl}/api/:path*`,
      },
      {
        source: '/admin/api/:path*',
        destination: `${apiBaseUrl}/admin/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;

