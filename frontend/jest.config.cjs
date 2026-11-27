/** Jest + ts-jest para pruebas de componentes React (TDD). */
module.exports = {
  testEnvironment: "jsdom",
  roots: ["<rootDir>/src"],
  setupFilesAfterEnv: ["<rootDir>/src/test/setup.ts"],
  transform: {
    "^.+\\.tsx?$": ["ts-jest", { tsconfig: "<rootDir>/tsconfig.jest.json" }],
  },
  moduleNameMapper: {
    "\\.(css|less|scss)$": "identity-obj-proxy",
    "^(\\.{1,2}/)+appConfig$": "<rootDir>/src/__mocks__/appConfig.ts",
  },
};
