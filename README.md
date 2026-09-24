# Analizador PF2025

Analizador léxico, sintáctico y semántico educativo en Python 3. Usa únicamente la biblioteca estándar. Las fases se ejecutan juntas; el programa analiza tipos y construye un AST, no ejecuta el código PF2025.

## Ejecutar

Desde esta carpeta:

```powershell
python src/analizador_lexico.py
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
| `salida/progfte.sem` | Tabla semántica: ámbito, declaraciones, valor propagado y errores |
| `salida/progfte.ast.json` | AST jerárquico con tipos, posiciones y valores constantes |
| `documentacion_semantica.md` | Informe editable |
| `docs/generar_pdf.py` | Generador del informe; requiere ReportLab |
| `output/pdf/Documentacion_PF2025.pdf` | Informe sin portada |

Los archivos de salida son generados automáticamente. El ejemplo conserva **292 tokens, 64 símbolos, 6 variables y 3 errores**: lectura incompatible en el renglón 13, división por cero en el 29 y operandos incompatibles en el 75.

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

Cada error se imprime con renglón, columna, tipo de error, tipos implicados y descripción; la fase (`Lexico`/`Sintactico`/`Semantico`) se conserva internamente para clasificación y orden. Las variables `Ent` asignadas a expresiones constantes propagan su valor: `a := 10; b := 2;` hace evaluable `a / b`, y un divisor calculado en cero (p. ej. `a / (b - 2)` con `b = 2`) se reporta como `Division por cero`; `leerdig`/`leercad` y las asignaciones dentro de `si`/`mientras` dejan el valor en desconocido. El valor final de cada variable se muestra en `progfte.sem` (`Valor:`) y la evaluación de cada operación, en `progfte.ast.json` (`valor`).

## Generar el informe

```powershell
python docs/generar_pdf.py
```

El informe se basa en la rúbrica U1 proporcionada, sin las dos restricciones de impresión indicadas y sin portada por solicitud del usuario. La reflexión personal propuesta debe adaptarse a la experiencia de cada integrante. La explicación individual y la entrega en plataforma son responsabilidad del equipo.
