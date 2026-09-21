# AGENTS.md

## Project
Lexical + semantic analyzer for the educational language **PF2025** (Lenguajes y Automatas course). All logic lives in one file, `src/analizador_lexico.py` — Python 3, stdlib only (`os`, `re`). No tests, linter, or build step exist.

## Commands
- Run the analyzer: `python3 src/analizador_lexico.py` (run from the project dir; paths resolve relative to the script location, so CWD is irrelevant).
- It reads `entrada/progfte.txt` and overwrites `salida/progfte.{dep,tab,tok,sem}` on every run. Treat `salida/` as generated output — never edit by hand.
- Verify by running the script and checking the trailer (`Total de errores`). With the current input this is 273 tokens and 3 errors total (rows 5, 65, 67).

## PF2025 quirks
- Case-sensitive. Reserved words: `pf2025 decl inicio fin si entonces sino finsi Ent cad Bool leerdig leercad impdig impcad verdadero falso y o no`.
- Comments `/* ... */` (multi-line) are stripped before tokenizing and never appear in output.
- Comment markers inside string literals are preserved as text; comment removal only applies outside quotes.
- Token refs: reserved words 100-120, operators/delimiters 500-514, identifiers 600+, integer constants 700+, string literals 800+. Duplicate lexemes reuse the same ref number.

## Gotchas
- NEVER modify `entrada/progfte.txt` — it is the fixed source input for the practice and grading.
- Errors from both phases are merged into a single list (`_errores_unificados`), one per line in `Renglon: N, Columna: N, Lexico|Semantico, Tipo de dato: X, descripcion` format, written to `.tok`, `.sem`, and console. `generar_tok` therefore runs AFTER semantic analysis and receives the semantic errors as an argument.
- `README.md` is stale: its token tables don't match the code, and its `docs/generar_pdf.py` regeneration step references a file that no longer exists. Trust the source over the README.
- String-literal contents are preserved verbatim; whitespace and separator normalization deliberately runs only outside quotes (`_limpiar_linea_fuera_cadenas`, `_normalizar_separadores_fuera_cadenas`).
- The glued-identifier delimiter set includes `!`, so `a!=b` is tokenized correctly without spaces.
- Identifiers must start with a letter. Glued-invalid lexemes (e.g. `nombre@Usuario`) and `_`-leading tokens each report exactly ONE error — the lexer consumes the whole bad lexeme (FIX #6).
- The semantic analyzer silently skips declaration lines that already had a lexical error (e.g. `cad nombre@Usuario;`), so the undeclared-variable error surfaces later when the variable is actually used in the body.
- Git: this folder is the repo root, branch `main`, remote `origin` → https://github.com/alevar30/Analizador.git.
- `documentacion_semantica.md` is a draft outline for the report's semantic-phase section (grammars, translation scheme, annotated trees, semantic actions).
