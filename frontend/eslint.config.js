import js from '@eslint/js';
import boundaries from 'eslint-plugin-boundaries';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import globals from 'globals';
import tseslint from 'typescript-eslint';

const SHARED_UI = ['atoms', 'molecules', 'organisms', 'templates'];

/** Allow `from` to import any of the given element types. */
const allow = (from, to) => ({
  from: { element: { type: from } },
  allow: { to: { element: { types: { anyOf: to } } } },
});

export default tseslint.config(
  { ignores: ['dist', 'coverage', 'src/lib/api/schema.d.ts'] },
  {
    files: ['**/*.{ts,tsx}'],
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    languageOptions: { globals: globals.browser },
    plugins: { 'react-hooks': reactHooks, 'react-refresh': reactRefresh },
    rules: {
      ...reactHooks.configs.recommended.rules,
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
      '@typescript-eslint/consistent-type-imports': 'error',
      '@typescript-eslint/no-explicit-any': 'error',
    },
  },

  // Architecture: imports flow app -> pages -> features -> shared layers, never back up.
  // See the react-architecture standard; a violation here means code is in the wrong folder.
  {
    files: ['src/**/*.{ts,tsx}'],
    plugins: { boundaries },
    settings: {
      'import/resolver': { typescript: { alwaysTryTypes: true } },
      'boundaries/elements': [
        { type: 'app', pattern: 'src/app' },
        { type: 'pages', pattern: 'src/pages/*' },
        { type: 'feature', pattern: 'src/features/*', capture: ['feature'] },
        { type: 'atoms', pattern: 'src/components/atoms/*' },
        { type: 'molecules', pattern: 'src/components/molecules/*' },
        { type: 'organisms', pattern: 'src/components/organisms/*' },
        { type: 'templates', pattern: 'src/components/templates/*' },
        { type: 'components', pattern: 'src/components' }, // the barrel: src/components/index.ts
        { type: 'shared', pattern: 'src/(hooks|lib|config|utils|types|styles)' },
        { type: 'test', pattern: 'src/test' },
        { type: 'entry', pattern: 'src' }, // main.tsx (first matching descriptor wins)
      ],
    },
    rules: {
      'boundaries/dependencies': [
        'error',
        {
          default: 'disallow',
          policies: [
            allow('entry', ['app', 'shared']),
            allow('app', ['app', 'pages', 'feature', 'components', ...SHARED_UI, 'shared']),
            allow('pages', ['feature', 'components', ...SHARED_UI, 'shared']),
            // A feature may import its own files, but other features only via pages.
            {
              from: { element: { type: 'feature' } },
              allow: {
                to: {
                  element: {
                    type: 'feature',
                    captured: { feature: '{{ from.element.captured.feature }}' },
                  },
                },
              },
            },
            allow('feature', ['components', ...SHARED_UI, 'shared']),
            allow('components', SHARED_UI),
            allow('templates', ['templates', 'organisms', 'molecules', 'atoms', 'shared']),
            allow('organisms', ['organisms', 'molecules', 'atoms', 'shared']),
            allow('molecules', ['molecules', 'atoms', 'shared']),
            allow('atoms', ['atoms', 'shared']),
            allow('shared', ['shared']),
            allow('test', ['test', 'shared', 'app', 'feature', 'components', ...SHARED_UI]),
          ],
        },
      ],
    },
  },
  {
    // Tests and test helpers may reach anywhere they need to.
    files: ['src/**/*.test.{ts,tsx}'],
    rules: { 'boundaries/dependencies': 'off' },
  },
  {
    files: ['*.config.{js,ts}'],
    languageOptions: { globals: globals.node },
  },
);
