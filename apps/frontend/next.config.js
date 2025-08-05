/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    // Ensure Turbo is properly configured
    turbo: {
      resolveAlias: {
        '@': './src',
      },
    },
  },
}

module.exports = nextConfig