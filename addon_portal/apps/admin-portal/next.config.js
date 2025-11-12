/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8080/api/:path*', // Use IPv4 to avoid IPv6 connection issues
      },
      {
        source: '/admin/api/:path*',
        destination: 'http://127.0.0.1:8080/admin/api/:path*', // Proxy admin API calls too
      },
    ];
  },
};

module.exports = nextConfig;

