# Analizador PF2025

Analizador léxico, sintáctico y semántico educativo en Python 3. Usa únicamente la biblioteca estándar. Las fases se ejecutan juntas; el programa analiza tipos y construye un AST, no ejecuta el código PF2025.

## Ejecutar

Desde esta carpeta:

```powershell
python src/analizador_lexico.py
python -B -m unittest discover -s tests -v
```

El analizador localiza sus archivos respecto a `src/analizador_lexico.py`, independientemente del directorio de ejecución. **No modificar `entrada/progfte.txt`**, entrada fija de la práctica.

## Archivos

| Archivo | Contenido |
|---|---|
| `src/analizador_lexico.py` | Analizador y generación de resultados |
| `entrada/progfte.txt` | Programa de referencia |
| `salida/progfte.dep` | Vista del código sin comentarios y con espacios normalizados |
| `salida/progfte.tab` | Tabla léxica: lexema, token y referencia |
| `salida/progfte.tok` | Tokens y errores unificados |
| `salida/progfte.sem` | Tabla semántica, ámbito, declaraciones y errores |
| `salida/progfte.ast.json` | AST jerárquico anotado con tipos y posiciones |
| `tests/test_rubrica.py` | 19 pruebas de aceptación, con casos adicionales por subprueba |
| `documentacion_semantica.md` | Informe editable |
| `docs/generar_pdf.py` | Generador del informe; requiere ReportLab |
| `output/pdf/Documentacion_PF2025.pdf` | Informe sin portada |

Los archivos de salida son generados automáticamente. El ejemplo conserva **273 tokens, 61 símbolos, 5 variables y 3 errores**: uno léxico en el renglón 5 y dos semánticos en los renglones 65 y 67.

## Lenguaje

```text
pf2025 nombre
decl
Ent contador;
Bool activo;
cad mensaje;
inicio
contador := 3;
activo := verdadero;
mientras contador > 0 y activo hacer
    impdig(contador);
    contador := contador - 1;
finmientras;
fin
```

- Tipos: `Ent`, `cad`, `Bool`; tipos internos: `ent`, `cad`, `bool`.
- Variables globales, declaradas antes de `inicio`; no se permiten declaraciones locales.
- Identificador: una letra seguida de letras o dígitos; `_` no permitido. Se admiten letras Unicode mediante `isalpha`/`isalnum`.
- Palabras reservadas originales: códigos 100-120; `mientras`, `hacer`, `finmientras`: 121-123.
- Operadores y delimitadores: 500-514. Identificadores: desde 600; enteros: desde 700; cadenas: desde 800.
- Condicional: `si ... entonces ... [sino ...] finsi`.
- Lectura: `leerdig(variableEnt)`, `leercad(variableCad)`.
- Impresión: `impcad(expresionCad)`. Por indicación de la práctica, **no se exige tipo de salida en `impdig` ni `impBool`**, aunque sus expresiones y variables sí se revisan.
- Cadenas de una línea entre comillas dobles, sin escapes. Comentarios `/* ... */`, no anidados.
- Columnas desde 1 sobre caracteres originales; un tabulador cuenta como un carácter.

Cada error incluye renglón, columna, fase, tipo de error, tipos implicados y descripción. Los errores de sintaxis se identifican como `Sintactico`, sin confundirlos con errores léxicos o semánticos.

## Generar el informe

```powershell
python docs/generar_pdf.py
```

El informe se basa en la rúbrica U1 proporcionada, sin las dos restricciones de impresión indicadas y sin portada por solicitud del usuario. La reflexión personal propuesta debe adaptarse a la experiencia de cada integrante. La explicación individual y la entrega en plataforma son responsabilidad del equipo.
