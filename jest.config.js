module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.js'],
  moduleNameMapping: {
    '\\.(css|less|scss)$': 'identity-obj-proxy',
  },
  transform: {
    '^.+\\.(js|jsx)$': 'babel-jest',
  },
  testMatch: [
    '<rootDir>/tests/frontend/**/*.test.{js,jsx}',
    '<rootDir>/tests/frontend/**/*.spec.{js,jsx}',
  ],
  collectCoverageFrom: [
    'components/**/*.{js,jsx}',
    'services/**/*.{js,jsx}',
    '!**/node_modules/**',
    '!**/dist/**',
  ],
  coverageDirectory: 'coverage-frontend',
  coverageReporters: ['text', 'lcov', 'html'],
};