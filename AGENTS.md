# AGENTS.md

## Project
Lexical + semantic analyzer for the educational language **PF2025** (Lenguajes y Automatas course). All logic lives in one file, `src/analizador_lexico.py` — Python 3, stdlib only (`os`, `re`). No tests, linter, or build step exist.

## Commands
- Run the analyzer: `python3 src/analizador_lexico.py` (run from the project dir; paths resolve relative to the script location, so CWD is irrelevant).
- It reads `entrada/progfte.txt` and overwrites `salida/progfte.{dep,tab,tok,sem}` on every run. Treat `salida/` as generated output — never edit by hand.
- Verify by running the script and checking the trailer (`Total de errores lexicos` / `Total de errores semanticos`). With the current input this is 273 tokens, 1 lexical error, and 2 semantic errors.

## PF2025 quirks
- Case-sensitive. Reserved words: `pf2025 decl inicio fin si entonces sino finsi Ent cad Bool leerdig leercad impdig impcad verdadero falso y o no`.
- Comments `/* ... */` (multi-line) are stripped before tokenizing and never appear in output.
- Token refs: reserved words 100-120, operators/delimiters 500-514, identifiers 600+, integer constants 700+, string literals 800+. Duplicate lexemes reuse the same ref number.

## Gotchas
- `README.md` is stale: its token tables don't match the code, and its `docs/generar_pdf.py` regeneration step references a file that no longer exists. Trust the source over the README.
- String-literal contents are preserved verbatim; whitespace-collapsing (`_limpiar_linea_fuera_cadenas`) deliberately skips text inside quotes.
- Identifiers must start with a letter. Glued-invalid lexemes (e.g. `nombre@Usuario`) and `_`-leading tokens each report exactly ONE error — the lexer consumes the whole bad lexeme (FIX #6).
- The semantic analyzer silently skips declaration lines that already had a lexical error (e.g. `cad nombre@Usuario;`), so the undeclared-variable error surfaces later when the variable is actually used in the body.
- Git: this folder is the repo root, branch `main`, remote `origin` → https://github.com/alevar30/Analizador.git.
- `documentacion_semantica.md` is a draft outline for the report's semantic-phase section (grammars, translation scheme, annotated trees, semantic actions).