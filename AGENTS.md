# AGENTS.md

## Project
Lexical + semantic analyzer for the educational language **PF2025** (Lenguajes y Automatas course). All logic lives in one file, `src/analizador_lexico.py` — Python 3, stdlib only (`os`, `re`, `json`). No tests, linter, or build step exist.

## Commands
- Run the analyzer: `python3 src/analizador_lexico.py` (run from the project dir; paths resolve relative to the script location, so CWD is irrelevant).
- It reads `entrada/progfte.txt` and overwrites `salida/progfte.{dep,tab,tok,sem,ast.json}` on every run. Treat `salida/` as generated output — never edit by hand.
- Verify by running the script and checking the trailer (`Total de errores`). With the current input this is 292 tokens, 64 symbols, 6 variables, and 3 errors (rows 13, 29, 75).

## PF2025 quirks
- Case-sensitive. Reserved words: `pf2025 decl inicio fin si entonces sino finsi Ent cad Bool leerdig leercad impdig impcad verdadero falso y o no impBool mientras hacer finmientras`.
- Comments `/* ... */` (multi-line) are stripped before tokenizing and never appear in output.
- Comment markers inside string literals are preserved as text; comment removal only applies outside quotes.
- Token refs: reserved words 100-123, operators/delimiters 500-514, identifiers 600+, integer constants 700+, string literals 800+. Duplicate lexemes reuse the same ref number.

## Gotchas
- NEVER modify `entrada/progfte.txt` unless the user explicitly authorizes the change — it is the fixed source input for the practice and grading.
- Errors from both phases are merged into a single list (`_errores_unificados`), one per line in `Renglon: N, Columna: N, Tipo de error: X, Tipo de dato: X, descripcion` format (the phase is not printed; it is kept internally for classification and sorting), written to `.tok`, `.sem`, and console. `generar_tok` therefore runs AFTER semantic analysis and receives the semantic errors as an argument.
- Constant propagation: an `Ent` variable assigned a constant expression stores its static `valor` in the semantic symbol table; `_valor_constante` reads it for `Variable` nodes. Division by a statically-known zero divisor (literal `0`, folded constants, or propagated variable values) is reported as `Division por cero` in `_reducir`. `leerdig`/`leercad` and assignments inside `si`/`mientras` blocks reset the value to unknown (conditional assignments must not propagate). The value is surfaced as `Valor:` in the `.sem` symbol table and every expression node in `.ast.json` carries a `valor` key (null when unknown).
- Original coordinates come from `lineas_lexicas` (comments replaced with spaces). `.dep` is only a normalized display. Tabs count as one character.
- Syntax diagnostics use phase `Sintactico`; semantic errors use `Semantico`.
- AST nodes are reduced on `pila_semantica`; completed expressions leave it balanced. The semantic symbol table stores global scope and declaration positions.
- Keep the requested exemptions: `impdig`/`impBool` do not restrict the final argument type, but still analyze the expression.
- PDF regeneration: `python docs/generar_pdf.py` requires ReportLab; output is `output/pdf/Documentacion_PF2025.pdf`. No cover per user request.
- String-literal contents are preserved verbatim; whitespace and separator normalization deliberately runs only outside quotes (`_limpiar_linea_fuera_cadenas`, `_normalizar_separadores_fuera_cadenas`).
- The glued-identifier delimiter set includes `!`, so `a!=b` is tokenized correctly without spaces.
- Identifiers must start with a letter. Glued-invalid lexemes (e.g. `nombre@Usuario`) and `_`-leading tokens each report exactly ONE error — the lexer consumes the whole bad lexeme (FIX #6).
- The semantic analyzer silently skips declaration lines that already had a lexical error (e.g. `cad nombre@Usuario;`), so the undeclared-variable error surfaces later when the variable is actually used in the body.
- Git: this folder is the repo root, branch `main`, remote `origin` → https://github.com/alevar30/Analizador.git.
- `documentacion_semantica.md` is the editable report source. Personal reflection is explicitly proposed text for the team to adapt.
