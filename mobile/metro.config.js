const { getDefaultConfig } = require('expo/metro-config');
const path = require('path');

const config = getDefaultConfig(__dirname);

// Force Metro to resolve modules from the mobile directory only
config.resolver.nodeModulesPaths = [path.resolve(__dirname, 'node_modules')];

// Watch only the mobile directory
config.watchFolders = [__dirname];

module.exports = config;
