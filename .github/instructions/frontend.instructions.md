---
applyTo: "**/*.{js,jsx,ts,tsx,html}"
---

# MRL Frontend Instructions

Apply these rules to all JavaScript, TypeScript, and HTML frontend code.

## Conventions
- Follow existing project style and formatting.
- Prefer TypeScript types where TypeScript is used.
- Keep components small and focused.
- Do not introduce placeholder or stub UI in place of required functionality.

## Security
- Never embed secrets, tokens, or credentials in frontend code or markup.
- Sanitize and validate any user-facing input.

## Validation
- Run available build, lint, and type-check commands (e.g. `npm run build`, `npm run lint`, `tsc`).
- Report exact commands executed and their results.

## Completion gate
- Return DELIVERY_PASS only when scope is fully covered, no placeholders exist, and validation passes or unavailable checks are justified.
