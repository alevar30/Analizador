#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================================================
 ANALIZADOR LEXICO - LENGUAJE PF2025
==============================================================================
 Instituto Tecnologico de Cd Guzman
 Departamento de Sistemas y Computacion
 Materia: Lenguajes y Automatas 1
 Profesor: Marco Antonio Guzman S.

 Descripcion:
 Este programa implementa un analizador lexico para el lenguaje de
 programacion PF2025. Lee un archivo fuente (progfte.txt), elimina
 comentarios y espacios innecesarios, genera el codigo depurado
 (progfte.dep), la tabla de simbolos (progfte.tab) y la lista de
 tokens (progfte.tok).

 Tokens reconocidos:
   - Palabras reservadas: pf2025, decl, inicio, fin, si, entonces, sino,
     finsi, Ent, cad, Bool, leerdig, leercad, impdig, impcad, verdadero,
     falso, y, o, no
   - Operadores aritmeticos: +, -, *, /
   - Operadores relacionales: >, <, >=, <=, ==, !=
   - Operador de asignacion: :=
   - Operadores logicos: y (and), o (or), no (not)
   - Simbolos especiales: (, ), ;, ,
   - Identificadores: letra(letra|digito)*
   - Constantes enteras: digito+
   - Cadenas literales: "..."
   - Comentarios: /* ... */ (se eliminan, no generan token)

==============================================================================
"""

import re
import os
import json

# ===========================================================================
# DEFINICION DE TOKENS Y TABLA DE SIMBOLOS
# ===========================================================================

# Diccionario de palabras reservadas y sus tokens asociados
# Cada palabra tiene su PROPIO numero unico (sin duplicados)
PALABRAS_RESERVADAS = {
    # --- Estructura del programa (100-107) ---
    'pf2025':      ('PROG',      100),
    'decl':        ('DECL',      101),
    'inicio':      ('INICIO',    102),
    'fin':         ('FIN',       103),
    'si':          ('SI',        104),
    'entonces':    ('ENTONCES',  105),
    'sino':        ('SINO',      106),
    'finsi':       ('FINSI',     107),
    # --- Tipos de datos (108-110) ---
    'Ent':         ('ENT',       108),
    'cad':         ('CAD',       109),
    'Bool':        ('BOOL',      110),
    # --- Entrada / Salida (111-115) ---
    'leerdig':     ('LEERDIG',   111),
    'leercad':     ('LEERCAD',   112),
    'impdig':      ('IMPDIG',    113),
    'impcad':      ('IMPCAD',    114),
    'impBool':     ('IMPBOOL',   115),
    # --- Constantes booleanas (116-117) ---
    'verdadero':   ('VERDADERO', 116),
    'falso':       ('FALSO',     117),
    # --- Operadores logicos (118-120) ---
    'y':           ('Y',         118),
    'o':           ('O',         119),
    'no':          ('NO',        120),
    'mientras':    ('MIENTRAS', 121),
    'hacer':       ('HACER', 122),
    'finmientras': ('FINMIENTRAS', 123),
}

# Diccionario de operadores y simbolos especiales
# Cada operador tiene su PROPIO numero unico (sin duplicados)
OPERADORES = {
    # --- Delimitadores (500-503) ---
    ';':  ('PC',      500),
    ',':  ('COMA',    501),
    '(':  ('PAREN',   502),
    ')':  ('TESIS',   503),
    # --- Operador de asignacion (504) ---
    ':=': ('ASIG',    504),
    # --- Operadores aritmeticos (505-508) ---
    '+':  ('MAS',     505),
    '-':  ('MENOS',   506),
    '*':  ('MUL',     507),
    '/':  ('DIV',     508),
    # --- Operadores relacionales (509-514) ---
    '>':  ('MAYOR',   509),
    '<':  ('MENOR',   510),
    '>=': ('MAYIG',   511),
    '<=': ('MENIG',   512),
    '==': ('EQU',     513),
    '!=': ('DIF',     514),
}

# Conjunto de operadores de un solo caracter (para busqueda rapida)
OPERADORES_1CHAR = set(k for k in OPERADORES if len(k) == 1)

# Contador para identificadores (comienza en 600)
id_counter = 600

# Contador para constantes enteras (comienza en 700)
cte_counter = 700

# Contador para cadenas literales (comienza en 800)
cad_counter = 800


class AnalizadorLexico:
    """
    Clase principal del analizador lexico para el lenguaje PF2025.
    Realiza el analisis lexico completo del programa fuente y genera
    los archivos de salida: .dep, .tab y .tok
    """

    def __init__(self, archivo_entrada):
        """
        Constructor: inicializa el analizador con el archivo fuente.
        Args:
            archivo_entrada (str): Ruta del archivo progfte.txt
        """
        self.archivo_entrada = archivo_entrada
        self.lineas_originales = []     # Lineas del archivo original
        self.codigo_depurado = []       # Lineas sin comentarios ni espacios extra
        self.tabla_simbolos = []        # Lista de simbolos reconocidos
        self.lista_tokens = []          # Lista de tokens con referencia de linea
        self.errores = []               # Lista de errores lexicos encontrados
        self.lexemas_set = set()        # Conjunto para evitar duplicados en tabla
        # FIX #1: Mapa lexema -> ref para busqueda O(1) en vez de recorrer toda la tabla
        self.lexema_a_ref = {}          # Diccionario de referencia rapida por lexema

    # =========================================================================
    # METODO 1: Lectura del archivo fuente
    # =========================================================================
    def leer_archivo(self):
        """
        Lee el archivo fuente y almacena cada linea con su numero de renglon.
        Maneja errores de lectura de archivo.
        """
        try:
            with open(self.archivo_entrada, 'r', encoding='utf-8') as f:
                self.lineas_originales = f.readlines()
            print(f"[OK] Archivo leido: {self.archivo_entrada}")
            print(f"[OK] Total de lineas: {len(self.lineas_originales)}")
        except FileNotFoundError:
            print(f"[ERROR] No se encontro el archivo: {self.archivo_entrada}")
            exit(1)
        except Exception as e:
            print(f"[ERROR] Error al leer el archivo: {e}")
            exit(1)

    # =========================================================================
    # METODO 2: Depuracion del codigo (eliminacion de comentarios y limpieza)
    # =========================================================================
    def _limpiar_linea_fuera_cadenas(self, linea):
        """
        Limpia espacios/tabuladores en una linea respetando el contenido
        dentro de cadenas literales entre comillas dobles.
        FIX #2 y #5: Antes se aplicaba re.sub a toda la linea incluyendo cadenas,
        lo cual destruia el contenido de las cadenas literales.
        """
        resultado = []
        dentro_cadena = False
        for ch in linea:
            if ch == '"' and not dentro_cadena:
                dentro_cadena = True
                resultado.append(ch)
            elif ch == '"' and dentro_cadena:
                dentro_cadena = False
                resultado.append(ch)
            elif dentro_cadena:
                # Dentro de cadena: preservar todo tal cual
                resultado.append(ch)
            else:
                # Fuera de cadena: reemplazar tab por espacio
                if ch == '\t':
                    resultado.append(' ')
                else:
                    resultado.append(ch)

        nueva_linea = ''.join(resultado)

        # Reducir multiples espacios a uno solo, pero solo fuera de cadenas
        # Usamos un metodo seguro que respeta las comillas
        partes = []
        dentro = False
        buffer = ""
        for ch in nueva_linea:
            if ch == '"':
                if dentro:
                    buffer += ch
                    partes.append(buffer)
                    buffer = ""
                    dentro = False
                else:
                    if buffer:
                        # Limpiar espacios multiples en la parte fuera de cadena
                        buffer = re.sub(r' +', ' ', buffer)
                        partes.append(buffer)
                        buffer = ""
                    buffer = ch
                    dentro = True
            elif dentro:
                buffer += ch
            else:
                buffer += ch

        if buffer:
            buffer = re.sub(r' +', ' ', buffer)
            partes.append(buffer)

        nueva_linea = ''.join(partes)
        return nueva_linea

    def _normalizar_separadores_fuera_cadenas(self, linea):
        """Normaliza separadores solo fuera de cadenas literales."""
        def normalizar(segmento):
            segmento = re.sub(r' +;', ';', segmento)
            segmento = re.sub(r' +,', ',', segmento)
            segmento = re.sub(r' +\)', ')', segmento)
            return re.sub(r'\( +', '(', segmento)

        partes = []
        buffer = []
        dentro_cadena = False

        for ch in linea:
            if ch == '"':
                if dentro_cadena:
                    buffer.append(ch)
                    partes.append(''.join(buffer))
                    buffer = []
                    dentro_cadena = False
                else:
                    if buffer:
                        partes.append(normalizar(''.join(buffer)))
                        buffer = []
                    buffer.append(ch)
                    dentro_cadena = True
            else:
                buffer.append(ch)

        if buffer:
            contenido = ''.join(buffer)
            partes.append(contenido if dentro_cadena else normalizar(contenido))

        return ''.join(partes)

    def depurar_codigo(self):
        """Enmascara comentarios sin desplazar las coordenadas originales.

        El lexer usa lineas_lexicas; .dep es solamente una vista normalizada.
        Las columnas cuentan caracteres desde 1 (un tabulador cuenta como uno).
        """
        self.lineas_lexicas = []
        self.codigo_depurado = []
        self.errores = []
        inicio_comentario = None
        for renglon, original in enumerate(self.lineas_originales, 1):
            linea = original.rstrip('\r\n')
            salida = list(linea)
            cadena = False
            j = 0
            while j < len(linea):
                par = linea[j:j + 2]
                if inicio_comentario:
                    salida[j] = ' '
                    if par == '*/':
                        salida[j:j + 2] = [' ', ' ']
                        inicio_comentario = None
                        j += 2
                    else:
                        j += 1
                elif not cadena and par == '/*':
                    inicio_comentario = (renglon, j + 1)
                    salida[j:j + 2] = [' ', ' ']
                    j += 2
                else:
                    if linea[j] == '"':
                        cadena = not cadena
                    j += 1
            limpia = ''.join(salida)
            self.lineas_lexicas.append(limpia)
            self.codigo_depurado.append(self._normalizar_separadores_fuera_cadenas(
                self._limpiar_linea_fuera_cadenas(limpia)).strip())
        if inicio_comentario:
            renglon, columna = inicio_comentario
            self.errores.append({'linea': renglon, 'columna': columna,
                'lexema': '/*', 'descripcion': 'Comentario sin cierre: se esperaba */'})
        print(f"[OK] Codigo depurado generado ({len(self.codigo_depurado)} lineas)")

    # =========================================================================
    # METODO 3: Generacion del archivo depurado (.dep)
    # =========================================================================
    def generar_dep(self, ruta_salida):
        """
        Escribe el codigo depurado al archivo progfte.dep.
        Solo incluye lineas que no esten completamente vacias.
        Args:
            ruta_salida (str): Ruta del archivo .dep
        """
        with open(ruta_salida, 'w', encoding='utf-8') as f:
            for linea in self.codigo_depurado:
                if linea.strip():  # Solo escribir lineas no vacias
                    f.write(linea + '\n')
        print(f"[OK] Archivo depurado generado: {ruta_salida}")

    # =========================================================================
    # METODO AUXILIAR: Registrar simbolo en tabla
    # =========================================================================
    def _registrar_simbolo(self, lexema, token, ref):
        """
        Registra un simbolo en la tabla si no existe.
        FIX #1: Actualiza tambien el mapa lexema_a_ref para busqueda O(1).
        """
        if lexema not in self.lexemas_set:
            self.tabla_simbolos.append({
                'no': len(self.tabla_simbolos) + 1,
                'lexema': lexema,
                'token': token,
                'ref': ref
            })
            self.lexemas_set.add(lexema)
            self.lexema_a_ref[lexema] = ref

    def _obtener_ref(self, lexema):
        """Obtiene la referencia de un lexema ya registrado. O(1) con el mapa."""
        return self.lexema_a_ref.get(lexema, None)

    # =========================================================================
    # METODO 4: Analisis lexico principal
    # =========================================================================
    def analizar(self):
        """
        Realiza el analisis lexico sobre las lineas con posiciones originales.
        Para cada linea, identifica tokens, palabras reservadas,
        identificadores, constantes, cadenas, operadores y errores.
        Almacena resultados en tabla_simbolos, lista_tokens y errores.
        """
        global id_counter, cte_counter, cad_counter

        self.lista_tokens.clear()
        self.tabla_simbolos.clear()
        self.lexemas_set.clear()
        self.lexema_a_ref.clear()
        id_counter = 600
        cte_counter = 700
        cad_counter = 800

        for num_linea, linea in enumerate(self.lineas_lexicas, 1):
            if not linea.strip():
                continue  # Saltar lineas vacias

            pos = 0
            n = len(linea)

            while pos < n:
                # --- Ignorar espacios ---
                if linea[pos].isspace():
                    pos += 1
                    continue

                # --- Detectar cadenas literales entre comillas ---
                if linea[pos] == '"':
                    columna = pos + 1
                    pos += 1
                    lexema_cadena = ""
                    while pos < n and linea[pos] != '"':
                        lexema_cadena += linea[pos]
                        pos += 1
                    if pos < n and linea[pos] == '"':
                        pos += 1  # Consumir la comilla de cierre
                    else:
                        # Error: cadena sin comilla de cierre
                        self.errores.append({
                            'linea': num_linea,
                            'columna': columna,
                            'lexema': lexema_cadena,
                            'descripcion': f'Cadena sin comilla de cierre: "{lexema_cadena}'
                        })
                        continue

                    lexema_completo = '"' + lexema_cadena + '"'
                    # FIX #1: Obtener referencia correcta de la cadena
                    ref_existente = self._obtener_ref(lexema_completo)
                    if ref_existente is None:
                        ref_existente = cad_counter
                        self._registrar_simbolo(lexema_completo, 'CAD_LIT', ref_existente)
                        cad_counter += 1
                    self.lista_tokens.append({
                        'renglon': num_linea,
                        'columna': columna,
                        'lexema': lexema_completo,
                        'token': 'CAD_LIT',
                        'token_num': ref_existente,  # FIX: ref correcta, no cad_counter-1
                        'descripcion': 'Cadena literal'
                    })
                    continue

                # --- Detectar operadores de dos caracteres ---
                # Orden importa: verificar primero los de 2 chars antes que los de 1
                dos_chars_posibles = {
                    ':': '=', '>': '=', '<': '=', '=': '=', '!': '='
                }
                if pos + 1 < n and linea[pos] in dos_chars_posibles:
                    columna = pos + 1
                    par = linea[pos] + linea[pos + 1]
                    if par in OPERADORES:
                        token_info = OPERADORES[par]
                        self._registrar_simbolo(par, token_info[0], token_info[1])
                        self.lista_tokens.append({
                            'renglon': num_linea,
                            'columna': columna,
                            'lexema': par,
                            'token': token_info[0],
                            'token_num': token_info[1],
                            'descripcion': f'Operador {token_info[0]}'
                        })
                        pos += 2
                        continue

                # --- Detectar operadores de un caracter ---
                if linea[pos] in OPERADORES_1CHAR:
                    columna = pos + 1
                    lexema_op = linea[pos]
                    token_info = OPERADORES[lexema_op]
                    self._registrar_simbolo(lexema_op, token_info[0], token_info[1])
                    self.lista_tokens.append({
                        'renglon': num_linea,
                        'columna': columna,
                        'lexema': lexema_op,
                        'token': token_info[0],
                        'token_num': token_info[1],
                        'descripcion': f'Operador {token_info[0]}'
                    })
                    pos += 1
                    continue

                # --- Detectar numeros enteros (constantes) ---
                if linea[pos].isdigit():
                    columna = pos + 1
                    inicio_num = pos
                    while pos < n and linea[pos].isdigit():
                        pos += 1
                    lexema_num = linea[inicio_num:pos]
                    if pos < n and (linea[pos].isalpha() or linea[pos] == '_'):
                        while pos < n and (linea[pos].isalnum() or linea[pos] == '_'):
                            pos += 1
                        self.errores.append({'linea': num_linea, 'columna': columna,
                            'lexema': linea[inicio_num:pos],
                            'descripcion': 'Identificador no valido: debe iniciar con letra'})
                        continue
                    # FIX #1: Obtener referencia correcta usando mapa O(1)
                    ref_existente = self._obtener_ref(lexema_num)
                    if ref_existente is None:
                        ref_existente = cte_counter
                        self._registrar_simbolo(lexema_num, 'CENT', ref_existente)
                        cte_counter += 1
                    self.lista_tokens.append({
                        'renglon': num_linea,
                        'columna': columna,
                        'lexema': lexema_num,
                        'token': 'CENT',
                        'token_num': ref_existente,
                        'descripcion': 'Constante entera'
                    })
                    continue

                # --- Detectar identificadores y palabras reservadas ---
                # FIX #3: Los identificadores SOLO pueden iniciar con letra (a-z, A-Z)
                # El guion bajo '_' NO es valido como primer caracter segun la ER del
                # lenguaje PF2025: id = letra(letra|digito)*
                if linea[pos].isalpha():
                    columna = pos + 1
                    inicio_id = pos
                    while pos < n and (linea[pos].isalnum() or linea[pos] == '_'):
                        pos += 1
                    lexema_id = linea[inicio_id:pos]

                    # FIX #6: Detectar caracteres invalidos pegados al identificador
                    # Ejemplo: nombre@Usuario → debe ser UN SOLO error, no dividirse
                    if pos < n and not linea[pos].isspace():
                        ch = linea[pos]
                        # Caracteres que pueden seguir a un identificador sin espacio
                        # (operadores, delimitadores, apertura de cadena)
                        seguidores_validos = set('()+-*/><=!;,\":')
                        if ch not in seguidores_validos:
                            # Caracter invalido pegado → consumir todo hasta el proximo
                            # espacio o delimitador y reportar como UN SOLO error
                            while (pos < n
                                   and not linea[pos].isspace()
                                   and linea[pos] not in seguidores_validos):
                                pos += 1
                            lexema_completo = linea[inicio_id:pos]
                            self.errores.append({
                                'linea': num_linea,
                                'columna': columna,
                                'lexema': lexema_completo,
                                'descripcion': f'Identificador no valido: {lexema_completo} (contiene caracteres no permitidos)'
                            })
                            continue

                    if '_' in lexema_id:
                        self.errores.append({'linea': num_linea, 'columna': columna,
                            'lexema': lexema_id,
                            'descripcion': f'Identificador no valido: {lexema_id} (no se permite _) '})
                        continue

                    # Verificar si es palabra reservada
                    if lexema_id in PALABRAS_RESERVADAS:
                        token_info = PALABRAS_RESERVADAS[lexema_id]
                        self._registrar_simbolo(lexema_id, token_info[0], token_info[1])
                        self.lista_tokens.append({
                            'renglon': num_linea,
                            'columna': columna,
                            'lexema': lexema_id,
                            'token': token_info[0],
                            'token_num': token_info[1],
                            'descripcion': f'Palabra reservada ({token_info[0]})'
                        })
                    else:
                        # Identificador valido (ya verificamos que inicia con letra)
                        ref_existente = self._obtener_ref(lexema_id)
                        if ref_existente is None:
                            ref_existente = id_counter
                            self._registrar_simbolo(lexema_id, 'id', ref_existente)
                            id_counter += 1
                        self.lista_tokens.append({
                            'renglon': num_linea,
                            'columna': columna,
                            'lexema': lexema_id,
                            'token': 'id',
                            'token_num': ref_existente,
                            'descripcion': 'Identificador'
                        })
                    continue

                # --- Identificador invalido (inicia con guion bajo) ---
                # FIX #3 mejorado: Si el caracter es _ seguido de alfanumericos,
                # consumir el lexema completo y reportarlo como un solo error
                if linea[pos] == '_' and pos + 1 < n and (linea[pos + 1].isalnum() or linea[pos + 1] == '_'):
                    columna = pos + 1
                    inicio_id = pos
                    while pos < n and (linea[pos].isalnum() or linea[pos] == '_'):
                        pos += 1
                    lexema_id = linea[inicio_id:pos]
                    self.errores.append({
                        'linea': num_linea,
                        'columna': columna,
                        'lexema': lexema_id,
                        'descripcion': f'Token identificador no valido: {lexema_id} (los identificadores deben iniciar con letra)'
                    })
                    continue

                # --- Caracter no identificado (error lexico) ---
                columna = pos + 1
                self.errores.append({
                    'linea': num_linea,
                    'columna': columna,
                    'lexema': linea[pos],
                    'descripcion': f'Simbolo no identificado: {linea[pos]} (posible error)'
                })
                pos += 1

        print(f"[OK] Analisis lexico completado")
        print(f"[OK] Tokens encontrados: {len(self.lista_tokens)}")
        print(f"[OK] Simbolos en tabla: {len(self.tabla_simbolos)}")
        print(f"[OK] Errores lexicos: {len(self.errores)}")

    # =========================================================================
    # METODO 5: Generacion de la tabla de simbolos (.tab)
    # =========================================================================
    def generar_tab(self, ruta_salida):
        """
        Genera el archivo de tabla de simbolos progfte.tab.
        Formato: No | LEXEMA | TOKEN | REF
        Args:
            ruta_salida (str): Ruta del archivo .tab
        """
        with open(ruta_salida, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("        TABLA DE SIMBOLOS - ANALIZADOR LEXICO PF2025\n")
            f.write("=" * 60 + "\n")
            f.write(f"{'No':<6} {'LEXEMA':<25} {'TOKEN':<15} {'REF':<6}\n")
            f.write("-" * 60 + "\n")
            for sim in self.tabla_simbolos:
                f.write(f"{sim['no']:<6} {sim['lexema']:<25} {sim['token']:<15} {sim['ref']:<6}\n")
            f.write("=" * 60 + "\n")
            f.write(f"Total de simbolos: {len(self.tabla_simbolos)}\n")
        print(f"[OK] Tabla de simbolos generada: {ruta_salida}")

    # =========================================================================
    # METODO 6: Generacion de la lista de tokens (.tok)
    # =========================================================================
    def generar_tok(self, ruta_salida, errores_semanticos=None):
        """
        Genera el archivo de lista de tokens progfte.tok.
        Incluye todos los tokens encontrados con su renglon de referencia,
        asi como la lista unificada de errores (lexicos y semanticos).
        Args:
            ruta_salida (str): Ruta del archivo .tok
            errores_semanticos (list): Errores del analizador semantico
        """
        errores = _errores_unificados(self.errores, errores_semanticos or [])
        with open(ruta_salida, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("     LISTA DE LEXEMAS Y TOKENS - ANALIZADOR LEXICO PF2025\n")
            f.write("=" * 70 + "\n\n")

            f.write("--- TOKENS RECONOCIDOS ---\n")
            f.write("-" * 70 + "\n")
            for tok in self.lista_tokens:
                f.write(f"Renglon: {tok['renglon']}, Lexema: {tok['lexema']}, "
                        f"Token: {tok['token_num']} {tok['token']}\n")

            f.write("\n" + "=" * 70 + "\n")
            f.write("--- ERRORES ---\n")
            f.write("-" * 70 + "\n")
            if errores:
                for err in errores:
                    f.write(_formatear_error(err) + '\n')
            else:
                f.write("No se encontraron errores.\n")

            f.write("\n" + "=" * 70 + "\n")
            f.write(f"Total de tokens: {len(self.lista_tokens)}\n")
            f.write(f"Total de errores: {len(errores)}\n")
        print(f"[OK] Lista de tokens generada: {ruta_salida}")

    # =========================================================================
    # METODO 7: Mostrar resultados en consola
    # =========================================================================
    def mostrar_resultados(self):
        """
        Muestra en consola los resultados del analisis lexico:
        tabla de simbolos y lista de tokens.
        """
        print("\n" + "=" * 60)
        print("           TABLA DE SIMBOLOS")
        print("=" * 60)
        print(f"{'No':<6} {'LEXEMA':<25} {'TOKEN':<15} {'REF':<6}")
        print("-" * 60)
        for sim in self.tabla_simbolos:
            print(f"{sim['no']:<6} {sim['lexema']:<25} {sim['token']:<15} {sim['ref']:<6}")
        print("=" * 60)

        print("\n" + "=" * 70)
        print("           LISTA DE TOKENS")
        print("=" * 70)
        for tok in self.lista_tokens:
            print(f"Renglon: {tok['renglon']}, Lexema: {tok['lexema']}, "
                  f"Token: {tok['token_num']} {tok['token']}")
        print("=" * 70)


# ===========================================================================
# ANALIZADOR SEMANTICO - LENGUAJE PF2025
# ===========================================================================

class AnalizadorSemantico:
    """Parser descendente: construye AST y comprueba tipos en una pasada.

    PF2025 declara variables exclusivamente en el bloque global `decl`.
    Cada primario apila un nodo tipado; cada operador reduce sus operandos.
    La sentencia consume el resultado, dejando la pila vacia.
    """
    TIPOS = {'ENT': 'ent', 'CAD': 'cad', 'BOOL': 'bool'}
    PRECEDENCIA = {'O': 1, 'Y': 2, 'EQU': 4, 'DIF': 4, 'MAYOR': 4,
                  'MENOR': 4, 'MAYIG': 4, 'MENIG': 4, 'MAS': 5,
                  'MENOS': 5, 'MUL': 6, 'DIV': 6}
    CIERRES = {'FIN', 'FINSI', 'SINO', 'FINMIENTRAS'}

    def __init__(self, lista_tokens, errores_lexicos):
        self.tokens = lista_tokens
        self.errores_lexicos = errores_lexicos
        self.lineas_con_error_lexico = {e['linea'] for e in errores_lexicos}
        self.pos = 0
        self.errores = []
        self.variables = {}
        self.tabla_simbolos = {}  # tipo, ambito y coordenadas de declaracion
        self.pila_semantica = []
        self.ast_sentencias = []
        self.ast = None

    def _actual(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        ultimo = self.tokens[-1] if self.tokens else {'renglon': 1, 'columna': 1, 'lexema': ''}
        return {'token': 'EOF', 'lexema': '', 'renglon': ultimo['renglon'],
                'columna': ultimo['columna'] + len(ultimo['lexema'])}

    def _tomar(self):
        tok = self._actual()
        if tok['token'] != 'EOF':
            self.pos += 1
        return tok

    def _aceptar(self, tipo):
        if self._actual()['token'] == tipo:
            return self._tomar()
        return None

    def _error(self, tok, clase, descripcion, esperado=None, obtenido=None, fase='Semantico'):
        self.errores.append({'renglon': tok['renglon'], 'columna': tok['columna'],
            'fase': fase, 'tipo_error': clase, 'tipo_esperado': esperado,
            'tipo_obtenido': obtenido,
            'tipo_dato': f"esperado: {esperado or 'no aplica'}; obtenido: {obtenido or 'desconocido'}",
            'descripcion': descripcion})

    def _esperar(self, tipo):
        tok = self._aceptar(tipo)
        if tok:
            return tok
        self._error(self._actual(), 'Sintaxis invalida', f'Se esperaba {tipo}',
                    fase='Sintactico')
        return self._actual()

    def _nodo(self, clase, tok, tipo=None, **datos):
        return dict(clase=clase, lexema=tok['lexema'], renglon=tok['renglon'],
                    columna=tok['columna'], tipo=tipo, **datos)

    def _tipo_variable(self, tok):
        simbolo = self.tabla_simbolos.get(tok['lexema'])
        if simbolo is None:
            self._error(tok, 'Variable no declarada',
                        f"Variable no declarada: {tok['lexema']}", obtenido='desconocido')
            return None
        return simbolo['tipo']

    def _comprobar(self, tok, esperado, obtenido, clase):
        # None propaga un error previo sin generar incompatibilidades en cascada.
        if obtenido is not None and obtenido != esperado:
            self._error(tok, clase, f'Se esperaba {esperado}, se obtuvo {obtenido}',
                        esperado, obtenido)

    def analizar(self):
        cabecera = self._esperar('PROG')
        nombre = self._esperar('id')
        declaraciones = []
        if self._aceptar('DECL'):
            while self._actual()['token'] not in {'INICIO', 'FIN', 'EOF'}:
                inicio = self.pos
                tipo_tok = self._tomar()
                if tipo_tok['token'] not in self.TIPOS:
                    self._error(tipo_tok, 'Declaracion invalida', 'Se esperaba Ent, cad o Bool', fase='Sintactico')
                    self._recuperar()
                    continue
                tipo = self.TIPOS[tipo_tok['token']]
                # Una declaracion lexicamente invalida no incorpora variables parciales.
                fin = self.pos
                while fin < len(self.tokens) and self.tokens[fin]['token'] not in {'PC', 'INICIO', 'FIN'}:
                    fin += 1
                tramo = self.tokens[inicio:min(fin + 1, len(self.tokens))]
                if any(t['renglon'] in self.lineas_con_error_lexico for t in tramo):
                    self.pos = fin
                    self._aceptar('PC')
                    continue
                while True:
                    if self._actual()['token'] != 'id':
                        self._esperar('id')
                        self._recuperar()
                        break
                    tok = self._tomar()
                    nombre_var = tok['lexema']
                    if nombre_var in self.tabla_simbolos:
                        self._error(tok, 'Variable declarada 2 veces',
                            f'Variable declarada 2 veces: {nombre_var}',
                            self.tabla_simbolos[nombre_var]['tipo'], tipo)
                    else:
                        self.variables[nombre_var] = tipo
                        self.tabla_simbolos[nombre_var] = dict(tipo=tipo, ambito='global',
                            renglon=tok['renglon'], columna=tok['columna'])
                    declaraciones.append(self._nodo('Declaracion', tok, tipo, ambito='global'))
                    if not self._aceptar('COMA'):
                        self._esperar('PC')
                        break
        self._esperar('INICIO')
        self.ast_sentencias = self._bloque({'FIN'})
        self._esperar('FIN')
        if self._actual()['token'] != 'EOF':
            self._error(self._actual(), 'Sintaxis invalida', 'Contenido despues de fin', fase='Sintactico')
        self.ast = self._nodo('Programa', cabecera, nombre=nombre['lexema'],
                             declaraciones=declaraciones, cuerpo=self.ast_sentencias)
        print(f'[OK] Variables declaradas: {len(self.variables)}')
        print(f'[OK] Errores de analisis sintactico/semantico: {len(self.errores)}')
        return self.errores

    def _recuperar(self):
        while self._actual()['token'] not in self.CIERRES | {'PC', 'EOF', 'INICIO'}:
            self._tomar()
        self._aceptar('PC')

    def _bloque(self, cierres):
        nodos = []
        while self._actual()['token'] not in cierres | self.CIERRES | {'EOF'}:
            inicio = self.pos
            nodo = self._sentencia()
            if nodo:
                nodos.append(nodo)
            if self.pos == inicio:  # Garantiza progreso incluso en entradas invalidas.
                self._tomar()
        return nodos

    def _sentencia(self):
        tok = self._tomar()
        clase = tok['token']
        if clase == 'id':
            tipo = self._tipo_variable(tok)
            self._esperar('ASIG')
            expr = self._expresion()
            if tipo is not None:
                self._comprobar(tok, tipo, expr['tipo'], 'Asignacion incompatible')
            self._esperar('PC')
            return self._nodo('Asignacion', tok, tipo, expresion=expr)
        if clase in {'LEERDIG', 'LEERCAD', 'IMPDIG', 'IMPCAD', 'IMPBOOL'}:
            self._esperar('PAREN')
            arg_tok = self._actual()
            expr = self._expresion()
            if clase in {'LEERDIG', 'LEERCAD'}:
                esperado = 'ent' if clase == 'LEERDIG' else 'cad'
                if expr['clase'] != 'Variable':
                    self._error(arg_tok, 'Argumento de lectura invalido',
                        'La lectura requiere una variable, no una expresion o literal', esperado, expr['tipo'])
                else:
                    self._comprobar(arg_tok, esperado, expr['tipo'], 'Tipo incompatible en lectura')
            elif clase == 'IMPCAD':
                self._comprobar(arg_tok, 'cad', expr['tipo'], 'Tipo incompatible en impresion')
            # impdig e impBool: se analiza el argumento, sin exigir un tipo particular.
            self._esperar('TESIS')
            self._esperar('PC')
            return self._nodo('Llamada', tok, argumento=expr)
        if clase in {'SI', 'MIENTRAS'}:
            expr = self._expresion()
            self._comprobar(tok, 'bool', expr['tipo'], 'Condicion incompatible')
            self._esperar('ENTONCES' if clase == 'SI' else 'HACER')
            cierre = 'FINSI' if clase == 'SI' else 'FINMIENTRAS'
            cuerpo = self._bloque({cierre, 'SINO'} if clase == 'SI' else {cierre})
            alternativo = []
            if clase == 'SI' and self._aceptar('SINO'):
                alternativo = self._bloque({'FINSI'})
            self._esperar(cierre)
            self._aceptar('PC')
            return self._nodo('Si' if clase == 'SI' else 'Mientras', tok,
                condicion=expr, cuerpo=cuerpo, alternativo=alternativo)
        self._error(tok, 'Sentencia invalida', f"Sentencia inesperada: {tok['lexema']}", fase='Sintactico')
        self._recuperar()
        return self._nodo('Error', tok)

    def _expresion(self):
        base = len(self.pila_semantica)
        self._subexpresion(1)
        resultado = self.pila_semantica.pop()
        assert len(self.pila_semantica) == base, 'Pila semantica desbalanceada'
        return resultado

    def _subexpresion(self, minimo):
        tok = self._actual()
        clase = tok['token']
        if clase in {'NO', 'MENOS'}:
            self._tomar()
            self._subexpresion(3 if clase == 'NO' else 7)
            self._reducir(tok, 1)
        elif clase == 'PAREN':
            self._tomar()
            self._subexpresion(1)
            self._esperar('TESIS')
            hijo = self.pila_semantica.pop()
            self.pila_semantica.append(self._nodo('Grupo', tok, hijo['tipo'], expresion=hijo))
        elif clase in {'id', 'CENT', 'CAD_LIT', 'VERDADERO', 'FALSO'}:
            self._tomar()
            tipo = self._tipo_variable(tok) if clase == 'id' else {
                'CENT': 'ent', 'CAD_LIT': 'cad', 'VERDADERO': 'bool', 'FALSO': 'bool'}[clase]
            self.pila_semantica.append(self._nodo('Variable' if clase == 'id' else 'Literal', tok, tipo))
        else:
            self._error(tok, 'Expresion incompleta', 'Se esperaba un operando', fase='Sintactico')
            self.pila_semantica.append(self._nodo('Error', tok))
        relacional = False
        while self.PRECEDENCIA.get(self._actual()['token'], 0) >= minimo:
            op = self._tomar()
            prioridad = self.PRECEDENCIA[op['token']]
            if prioridad == 4 and relacional:
                self._error(op, 'Comparacion encadenada', 'Use y/o para combinar comparaciones', fase='Sintactico')
            relacional = relacional or prioridad == 4
            self._subexpresion(prioridad + 1)
            self._reducir(op, 2)

    def _valor_constante(self, nodo):
        """Valor entero estatico de un nodo; None si depende de variables o ya contiene un error."""
        if nodo['clase'] == 'Literal' and nodo['tipo'] == 'ent':
            return int(nodo['lexema'])
        if nodo['clase'] == 'Grupo':
            return self._valor_constante(nodo['expresion'])
        if nodo['clase'] == 'Unario' and nodo['lexema'] == '-':
            valor = self._valor_constante(nodo['hijos'][0])
            return None if valor is None else -valor
        if nodo['clase'] == 'Binario' and nodo['lexema'] in ('+', '-', '*', '/'):
            izquierda = self._valor_constante(nodo['hijos'][0])
            derecha = self._valor_constante(nodo['hijos'][1])
            if izquierda is None or derecha is None:
                return None
            if nodo['lexema'] == '+':
                return izquierda + derecha
            if nodo['lexema'] == '-':
                return izquierda - derecha
            if nodo['lexema'] == '*':
                return izquierda * derecha
            if derecha == 0:  # division por cero interna ya reportada
                return None
            return izquierda // derecha
        return None

    def _reducir(self, op, aridad):
        """Consume operandos reales de la pila y apila el AST tipado resultante."""
        hijos = [self.pila_semantica.pop() for _ in range(aridad)][::-1]
        tipos = [h['tipo'] for h in hijos]
        clase = op['token']
        esperado = 'bool' if clase in {'Y', 'O', 'NO'} else 'ent'
        igualdad = clase in {'EQU', 'DIF'}
        resultado = None
        if all(t is not None for t in tipos):
            valido = len(set(tipos)) == 1 if igualdad else all(t == esperado for t in tipos)
            if valido:
                resultado = 'bool' if igualdad or clase in {'Y', 'O', 'NO', 'MAYOR', 'MENOR', 'MAYIG', 'MENIG'} else 'ent'
            else:
                self._error(op, 'Operandos incompatibles', f"Operandos invalidos para {op['lexema']}",
                    'mismo tipo' if igualdad else '/'.join([esperado] * aridad), '/'.join(tipos))
        if clase == 'DIV' and self._valor_constante(hijos[1]) == 0:
            self._error(op, 'Division por cero', 'Division por cero: no se puede dividir entre cero',
                        'divisor distinto de cero', '0')
        self.pila_semantica.append(self._nodo('Unario' if aridad == 1 else 'Binario',
                                            op, resultado, hijos=hijos))

    def generar_sem(self, ruta_salida):
        errores = _errores_unificados(self.errores_lexicos, self.errores)
        with open(ruta_salida, 'w', encoding='utf-8') as f:
            f.write('ANALISIS SEMANTICO PF2025\n\n--- TABLA DE SIMBOLOS SEMANTICA ---\n')
            for nombre, simbolo in self.tabla_simbolos.items():
                f.write(f"Variable: {nombre}, Tipo: {simbolo['tipo']}, Ambito: {simbolo['ambito']}, "
                        f"Declaracion: {simbolo['renglon']}:{simbolo['columna']}\n")
            f.write(f'Total de variables declaradas: {len(self.variables)}\n\n--- ERRORES ---\n')
            for error in errores:
                f.write(_formatear_error(error) + '\n')
            if not errores:
                f.write('No se encontraron errores.\n')
            f.write(f'Total de errores: {len(errores)}\n')
        # AST anotado, serializable y revisable para la entrega.
        with open(os.path.splitext(ruta_salida)[0] + '.ast.json', 'w', encoding='utf-8') as f:
            json.dump(self.ast, f, ensure_ascii=False, indent=2)


def _errores_unificados(errores_lexicos, errores_semanticos):
    """Preserva clasificacion, tipos y coordenadas de las tres fases."""
    unificados = []
    for error in errores_lexicos:
        descripcion = error['descripcion']
        clase = ('Comentario sin cierre' if descripcion.startswith('Comentario') else
                 'Cadena sin cierre' if descripcion.startswith('Cadena') else
                 'Identificador invalido' if 'identificador' in descripcion.lower() else
                 'Simbolo no reconocido')
        unificados.append(dict(renglon=error['linea'], columna=error['columna'],
            fase='Lexico', tipo_error=clase, tipo_dato='no aplica',
            tipo_esperado=None, tipo_obtenido=None, descripcion=descripcion))
    unificados.extend(dict(error) for error in errores_semanticos)
    return sorted(unificados, key=lambda e: (e['renglon'], e['columna']))


def _formatear_error(error):
    return (f"Renglon: {error['renglon']}, "
            f"Tipo de error: {error['tipo_error']}, "
            f"Tipo de dato: {error['tipo_dato']}, {error['descripcion']}")


# ===========================================================================
# FUNCION PRINCIPAL
# ===========================================================================
def main():
    """
    Funcion principal que ejecuta todo el proceso del analizador:
    1. Lee el archivo fuente (progfte.txt)
    2. Depura el codigo (elimina comentarios, espacios)
    3. Genera progfte.dep
    4. Realiza el analisis lexico
    5. Realiza el analisis semantico
    6. Genera progfte.tab
    7. Genera progfte.tok
    8. Genera progfte.sem
    """
    print("=" * 70)
    print("    ANALIZADOR LEXICO - LENGUAJE DE PROGRAMACION PF2025")
    print("    Instituto Tecnologico de Cd Guzman")
    print("=" * 70)
    print()

    # Definir rutas de archivos (relativas a la raiz del proyecto)
    directorio_src = os.path.dirname(os.path.abspath(__file__))
    directorio_proyecto = os.path.dirname(directorio_src)
    carpeta_entrada = os.path.join(directorio_proyecto, 'entrada')
    carpeta_salida = os.path.join(directorio_proyecto, 'salida')

    archivo_entrada = os.path.join(carpeta_entrada, 'progfte.txt')
    archivo_dep = os.path.join(carpeta_salida, 'progfte.dep')
    archivo_tab = os.path.join(carpeta_salida, 'progfte.tab')
    archivo_tok = os.path.join(carpeta_salida, 'progfte.tok')
    archivo_sem = os.path.join(carpeta_salida, 'progfte.sem')

    os.makedirs(carpeta_salida, exist_ok=True)

    # Crear instancia del analizador lexico
    analizador = AnalizadorLexico(archivo_entrada)

    # Paso 1: Leer archivo fuente
    print("\n--- PASO 1: Lectura del archivo fuente ---")
    analizador.leer_archivo()

    # Paso 2: Depurar codigo (eliminar comentarios y limpiar)
    print("\n--- PASO 2: Depuracion del codigo ---")
    analizador.depurar_codigo()

    # Paso 3: Generar archivo depurado
    print("\n--- PASO 3: Generacion de archivo .dep ---")
    analizador.generar_dep(archivo_dep)

    # Paso 4: Analisis lexico
    print("\n--- PASO 4: Analisis lexico ---")
    analizador.analizar()

    # Paso 5: Analisis semantico
    print("\n--- PASO 5: Analisis semantico ---")
    analizador_semantico = AnalizadorSemantico(analizador.lista_tokens, analizador.errores)
    analizador_semantico.analizar()

    # Paso 6: Generar tabla de simbolos
    print("\n--- PASO 6: Generacion de tabla de simbolos .tab ---")
    analizador.generar_tab(archivo_tab)

    # Paso 7: Generar lista de tokens
    print("\n--- PASO 7: Generacion de lista de tokens .tok ---")
    analizador.generar_tok(archivo_tok, analizador_semantico.errores)

    # Paso 8: Generar analisis semantico
    print("\n--- PASO 8: Generacion de analisis semantico .sem ---")
    analizador_semantico.generar_sem(archivo_sem)

    # Mostrar resultados
    print("\n--- RESULTADOS ---")
    analizador.mostrar_resultados()

    errores = _errores_unificados(analizador.errores, analizador_semantico.errores)
    print("\n" + "=" * 70)
    print("           ERRORES")
    print("=" * 70)
    if errores:
        for err in errores:
            print(_formatear_error(err))
    else:
        print("No se encontraron errores.")
    print("=" * 70)

    print("\n" + "=" * 70)
    print("    ANALISIS FINALIZADO")
    print(f"    Archivos generados en: {carpeta_salida}")
    print(f"    Total de errores: {len(errores)}")
    print("=" * 70)


if __name__ == "__main__":
    main()
