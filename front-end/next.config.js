/** @type {import('next').NextConfig} */
const nextConfig = {
  webpack: (config) => {
    config.externals = [...config.externals, 'multer'];
    return config;
  },
};

export default nextConfig;