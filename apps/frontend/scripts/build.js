#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Create symbolic link to ensure lib directory is accessible
const srcPath = path.resolve(__dirname, '../src');
const libPath = path.resolve(srcPath, 'lib');

console.log('Pre-build: Setting up module resolution...');
console.log('Source path:', srcPath);
console.log('Lib path:', libPath);

if (fs.existsSync(libPath)) {
  console.log('Lib directory exists');
  console.log('Contents:', fs.readdirSync(libPath));
} else {
  console.error('ERROR: Lib directory does not exist!');
  process.exit(1);
}

// Run the actual build
console.log('Running Next.js build...');
try {
  execSync('next build', { stdio: 'inherit', cwd: path.resolve(__dirname, '..') });
  console.log('Build completed successfully!');
} catch (error) {
  console.error('Build failed:', error.message);
  process.exit(1);
}