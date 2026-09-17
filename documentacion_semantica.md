# Documentación — Fase de Análisis Semántico (PF2025)

> Borrador/esqueleto para la sección del informe. Completa las secciones marcadas como *(redactar)* y pégalo en el documento PDF de entrega.

## 1. Introducción

El análisis semántico se implementa como una segunda pasada sobre la lista de tokens generada por el analizador léxico (clase `AnalizadorSemantico`, en `src/analizador_lexico.py`). Trabaja en una sola pasada y verifica, reportando **renglón y columna**:

- que todas las variables usadas estén declaradas;
- que ninguna variable se declare dos veces;
- los tipos de las expresiones (aritméticas, relacionales y lógicas);
- que las asignaciones respeten el tipo de la variable;
- que las condiciones de `si` (y `mientras`) sean de tipo `bool`;
- que los argumentos de `leerdig`, `leercad` e `impcad` sean válidos.

## 2. Gramática de sentencias

```
<programa>         ::= pf2025 <id> [ decl <declaraciones> ] inicio <sentencias> fin
<declaraciones>    ::= <tipo> <lista_ids> ; { <tipo> <lista_ids> ; }
<lista_ids>        ::= <id> { , <id> }
<tipo>             ::= Ent | cad | Bool
<sentencias>       ::= { <sentencia> }
<sentencia>        ::= <asignacion> | <llamada> | <condicional> | <bucle>
<asignacion>       ::= <id> := <expresion> ;
<llamada>          ::= leerdig ( <id> ) ; | leercad ( <id> ) ;
                      | impdig ( <expresion> ) ; | impBool ( <expresion> ) ;
                      | impcad ( <expresion> ) ;
<condicional>      ::= si <expresion> entonces <sentencias>
                       [ sino <sentencias> ] finsi [ ; ]
<bucle>            ::= mientras <expresion> hacer <sentencias> finmientras [ ; ]
```

## 3. Gramática de expresiones (precedencia de menor a mayor)

```
<expresion>      ::= <or>
<or>             ::= <and> { o <and> }
<and>            ::= <not> { y <not> }
<not>            ::= no <not> | <relacional>
<relacional>     ::= <adicion> [ <op_rel> <adicion> ]
<op_rel>         ::= == | != | > | < | >= | <=
<adicion>        ::= <multiplicacion> { ( + | - ) <multiplicacion> }
<multiplicacion> ::= <unario> { ( * | / ) <unario> }
<unario>         ::= - <unario> | <primario>
<primario>       ::= <id> | <CENT> | <CAD_LIT> | verdadero | falso | ( <expresion> )
```

## 4. Reglas de tipos y acciones semánticas (esquema de traducción)

La pila semántica guarda el tipo de cada operando; por cada operador se extraen los operandos, se comprueban y se determina el tipo resultado. Los errores se reportan con renglón y columna; cuando una variable no declarada produce un tipo inválido se evitan errores en cascada.

| Regla gramatical | Acción semántica | Tipo resultado |
|---|---|---|
| `<CENT>` | push ent | ent |
| `<CAD_LIT>` | push cad | cad |
| `verdadero` / `falso` | push bool | bool |
| `<id>` | push tipo de su declaración; error "Variable no declarada" si no existe | tipo declarado |
| `( E )` | propaga | tipo de E |
| `- E` | E debe ser ent | ent |
| `E1 + E2`, `E1 - E2`, `E1 * E2`, `E1 / E2` | ambos operandos ent | ent |
| `E1 == E2`, `E1 != E2` | ambos operandos del mismo tipo | bool |
| `E1 > E2`, `E1 < E2`, `E1 >= E2`, `E1 <= E2` | ambos operandos ent | bool |
| `E1 y E2`, `E1 o E2` | ambos operandos bool | bool |
| `no E` | E debe ser bool | bool |
| `<id> := E ;` | tipo de E == tipo del id | — |
| `si E entonces ...` | E debe ser bool | — |
| `leerdig ( <id> )` | el id debe ser ent | — |
| `leercad ( <id> )` | el id debe ser cad | — |
| `impcad ( E )` | E debe ser cad | — |
| `impdig ( E )`, `impBool ( E )` | sin comprobación de tipo (decisión de diseño) | — |

## 5. Árboles anotados de ejemplo

`resultado := a + b;`

```
             :=   (ent = ent, válido)
           /    \
      resultado      +
         (ent)     /   \
                 a     b
               (ent)  (ent)
```

`si a > b y b > 0 entonces ...`

```
              si    (bool, válido)
               |
              y     (bool)
            /     \
           >       >     (bool, bool)
          / \     / \
         a   b   b   0
       (ent)(ent)(ent)(ent)
```

## 6. Pruebas y resultados (programa `entrada/progfte.txt`)

Variables declaradas: `a` (ent), `b` (ent), `resultado` (ent), `esValido` (bool), `terminado` (bool) → 5 variables.

La línea `cad nombre@Usuario;` provoca un error léxico y su declaración se omite, por lo que `nombreUsuario` queda sin declarar. Errores semánticos reportados en `salida/progfte.sem`:

```
Renglon: 65, Columna: 9, Variable no declarada: nombreUsuario
Renglon: 67, Columna: 8, Variable no declarada: nombreUsuario
Total de errores semanticos: 2
```

*(redactar)* Comparación de las verificaciones pedidas en la rúbrica U1 con lo implementado y una conclusión personal.

## 7. Conclusiones

*(redactar)*