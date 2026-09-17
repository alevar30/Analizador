# Analizador Lexico - Lenguaje PF2025

**Instituto Tecnologico de Cd Guzman**
**Materia:** Lenguajes y Automatas 1
**Profesor:** Marco Antonio Guzman S.

---

## Descripcion

Analizador lexico implementado en Python 3 para el lenguaje de programacion educativo **PF2025**.
Lee un programa fuente, elimina comentarios, reconoce tokens, detecta errores lexicos y genera
los archivos de salida requeridos: `.dep`, `.tab` y `.tok`.

## Estructura del Proyecto

```
AnalizadorLexico_PF2025/
|
|-- src/                              # Codigo fuente
|   |-- analizador_lexico.py          # Analizador lexico principal
|
|-- entrada/                          # Archivos de entrada
|   |-- progfte.txt                   # Programa fuente en PF2025
|
|-- salida/                           # Archivos generados por el analizador
|   |-- progfte.dep                   # Codigo depurado (sin comentarios)
|   |-- progfte.tab                   # Tabla de simbolos
|   |-- progfte.tok                   # Lista de tokens
|
|-- docs/                             # Documentacion
|   |-- generar_pdf.py                # Script para generar el PDF
|   |-- Documentacion_Analizador_Lexico_PF2025.pdf
|
|-- README.md                         # Este archivo
```

## Como Ejecutar

### Ejecutar el analizador lexico

```bash
cd AnalizadorLexico_PF2025
python3 src/analizador_lexico.py
```

Esto leera `entrada/progfte.txt` y generara los archivos en la carpeta `salida/`.

### Regenerar la documentacion PDF

```bash
cd AnalizadorLexico_PF2025
python3 docs/generar_pdf.py
```

El PDF se guardara en `docs/Documentacion_Analizador_Lexico_PF2025.pdf`.

## Tokens Reconocidos

| Categoria        | Tokens                                                       | Codigos    |
|------------------|--------------------------------------------------------------|------------|
| Palabras Reserv. | pf2025, decl, inicio, fin, end, if, then, do, while          | 100-108    |
| Tipos de Datos   | Ent, cad, Bool, booleano                                     | 200        |
| Entrada/Salida   | leerdig, leercad, impdig, impcad, impBool                    | 300-304    |
| Constantes Bool  | true, false                                                   | 400-401    |
| Operadores       | ; , := + - * / ( ) =                                         | 500-509    |
| Identificadores  | letra(letra\|digito)*                                         | 600+       |
| Constantes Ent.  | digito+                                                       | 700+       |
| Cadenas Literales| "...\"                                                         | 800+       |

## Lenguaje PF2025

- **Estructura:** `pf2025 <nombre> [decl <variables>] inicio <sentencias> fin`
- **Tipos:** Ent (entero), cad (cadena), Bool (booleano)
- **Comentarios:** `/* ... */` (multilinea)
- **Asignacion:** `:=`
- **Sensible a mayusculas/minusculas**
