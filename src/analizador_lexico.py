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
        """
        Elimina comentarios del tipo /* ... */ y limpia espacios innecesarios
        (tabuladores, multiples espacios). Genera el codigo depurado que
        se guardara en progfte.dep.
        El analizador soporta comentarios multinea.
        FIX #2/#5: La limpieza de espacios ahora respeta el contenido de
        las cadenas literales para no alterarlas.
        """
        dentro_comentario = False
        codigo_depurado_lineas = []

        for i, linea in enumerate(self.lineas_originales, 1):
            nueva_linea = ""
            j = 0
            dentro_cadena = False
            while j < len(linea):
                if dentro_comentario:
                    # Dentro de un comentario, las comillas no cambian el estado.
                    if j + 1 < len(linea) and linea[j] == '*' and linea[j + 1] == '/':
                        dentro_comentario = False
                        j += 2
                    else:
                        j += 1
                    continue

                if linea[j] == '"':
                    nueva_linea += linea[j]
                    j += 1
                    dentro_cadena = not dentro_cadena
                    continue

                # Detectar inicio de comentario /*
                if (not dentro_cadena and j + 1 < len(linea)
                        and linea[j] == '/' and linea[j + 1] == '*'):
                    dentro_comentario = True
                    j += 2  # Saltar los caracteres /*
                    continue

                # Caracter normal: agregarlo
                nueva_linea += linea[j]
                j += 1

            # Limpiar la linea respetando cadenas literales
            nueva_linea = self._limpiar_linea_fuera_cadenas(nueva_linea)

            # Eliminar espacios al inicio y final de la linea (fuera de cadenas)
            nueva_linea = nueva_linea.strip()
            nueva_linea = self._normalizar_separadores_fuera_cadenas(nueva_linea)

            codigo_depurado_lineas.append(nueva_linea)

        self.codigo_depurado = codigo_depurado_lineas
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
        Realiza el analisis lexico completo del codigo depurado.
        Para cada linea, identifica tokens, palabras reservadas,
        identificadores, constantes, cadenas, operadores y errores.
        Almacena resultados en tabla_simbolos, lista_tokens y errores.
        """
        global id_counter, cte_counter, cad_counter

        id_counter = 600
        cte_counter = 700
        cad_counter = 800

        for num_linea, linea in enumerate(self.codigo_depurado, 1):
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
                    f.write(f"Renglon: {err['renglon']}, Columna: {err['columna']}, "
                            f"{err['fase']}, Tipo de dato: {err['tipo_dato']}, "
                            f"{err['descripcion']}\n")
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
    """
    Analizador semantico para el lenguaje PF2025.
    Realiza comprobaciones de tipos, variables declaradas,
    y validacion de sentencias en una sola pasada sobre la lista
    de tokens generada por el analizador lexico.
    Utiliza una pila semantica para evaluar tipos de expresiones.
    """

    def __init__(self, lista_tokens, errores_lexicos):
        self.tokens = lista_tokens
        self.pos = 0
        self.errores = []
        self.variables = {}
        self.pila_semantica = []
        self.ast_sentencias = []
        self.errores_lexicos = errores_lexicos
        self.lineas_con_error_lexico = set(
            e['linea'] for e in errores_lexicos
        )

    def _token_actual(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def _avanzar(self):
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def _error(self, renglon, columna, descripcion, tipo_error, tipo_dato):
        self.errores.append({
            'renglon': renglon,
            'columna': columna,
            'tipo_error': tipo_error,
            'tipo_dato': tipo_dato,
            'descripcion': descripcion
        })

    def _saltar_hasta(self, tipos):
        while self._token_actual() and self._token_actual()['token'] not in tipos:
            self._avanzar()

    def analizar(self):
        self._parsear_encabezado()
        self._parsear_declaraciones()
        self._parsear_cuerpo()
        print(f"[OK] Analisis semantico completado")
        print(f"[OK] Variables declaradas: {len(self.variables)}")
        print(f"[OK] Errores semanticos: {len(self.errores)}")
        return self.errores

    def _parsear_encabezado(self):
        tok = self._token_actual()
        if tok and tok['token'] == 'PROG':
            self._avanzar()
            if self._token_actual() and self._token_actual()['token'] == 'id':
                self._avanzar()

    def _parsear_declaraciones(self):
        tok = self._token_actual()
        if not tok or tok['token'] != 'DECL':
            return
        self._avanzar()

        while True:
            tok = self._token_actual()
            if not tok or tok['token'] in ('INICIO', 'FIN'):
                break
            if tok['token'] in ('ENT', 'CAD', 'BOOL'):
                tipo_tok = self._avanzar()
                tipo = {'ENT': 'ent', 'CAD': 'cad', 'BOOL': 'bool'}[tipo_tok['token']]
                self._parsear_lista_ids(tipo)
            elif tok['token'] == 'PC':
                self._avanzar()
            else:
                break

    def _parsear_lista_ids(self, tipo):
        while True:
            tok = self._token_actual()
            if not tok:
                break
            if tok['token'] == 'id':
                self._avanzar()
                nombre = tok['lexema']
                if nombre in self.variables:
                    self._error(tok['renglon'], tok['columna'],
                                f"Variable declarada 2 veces: {nombre}",
                                "Variable declarada 2 veces", tipo)
                else:
                    self.variables[nombre] = tipo
                sig = self._token_actual()
                if sig and sig['token'] == 'COMA':
                    self._avanzar()
                elif sig and sig['token'] == 'PC':
                    self._avanzar()
                    break
                else:
                    if tok['renglon'] in self.lineas_con_error_lexico:
                        self._saltar_hasta(('PC',))
                        if self._token_actual() and self._token_actual()['token'] == 'PC':
                            self._avanzar()
                    break
            elif tok['token'] == 'PC':
                self._avanzar()
                break
            elif tok['renglon'] in self.lineas_con_error_lexico:
                self._saltar_hasta(('PC',))
                if self._token_actual() and self._token_actual()['token'] == 'PC':
                    self._avanzar()
                break
            else:
                self._error(tok['renglon'], tok['columna'],
                            "Se esperaba un identificador en la declaracion",
                            "Error de sintaxis", "-")
                self._saltar_hasta(('PC',))
                if self._token_actual() and self._token_actual()['token'] == 'PC':
                    self._avanzar()
                break

    def _parsear_cuerpo(self):
        tok = self._token_actual()
        if tok and tok['token'] == 'INICIO':
            self._avanzar()
        while True:
            tok = self._token_actual()
            if not tok or tok['token'] == 'FIN':
                break
            self._parsear_sentencia()

    def _parsear_sentencia(self):
        tok = self._token_actual()
        if not tok:
            return

        if tok['token'] == 'id':
            self._parsear_asignacion()
        elif tok['token'] in ('LEERDIG', 'LEERCAD', 'IMPDIG', 'IMPCAD', 'IMPBOOL'):
            self._parsear_llamada_funcion()
        elif tok['token'] == 'SI':
            self._parsear_condicional()
        elif tok['token'] == 'MIENTRAS':
            self._parsear_bucle()
        else:
            self._saltar_hasta(('PC',))
            if self._token_actual() and self._token_actual()['token'] == 'PC':
                self._avanzar()

    def _parsear_asignacion(self):
        id_tok = self._avanzar()
        sig = self._token_actual()
        if sig and sig['token'] == 'ASIG':
            self._avanzar()
            tipo_expr = self._parsear_expresion()
            if id_tok['lexema'] not in self.variables:
                self._error(id_tok['renglon'], id_tok['columna'],
                            f"Variable no declarada: {id_tok['lexema']}",
                            "Variable no declarada", "desconocido")
            elif tipo_expr is not None and self.variables[id_tok['lexema']] != tipo_expr:
                self._error(id_tok['renglon'], id_tok['columna'],
                            f"Error de tipo en asignacion: se esperaba "
                            f"'{self.variables[id_tok['lexema']]}', se obtuvo '{tipo_expr}'",
                            "Error de tipo en asignacion",
                            f"se esperaba '{self.variables[id_tok['lexema']]}', "
                            f"se obtuvo '{tipo_expr}'")
            if self._token_actual() and self._token_actual()['token'] == 'PC':
                self._avanzar()
        else:
            self._error(id_tok['renglon'], id_tok['columna'],
                        "Se esperaba ':=' despues del identificador",
                        "Error de sintaxis", "-")
            self._saltar_hasta(('PC',))
            if self._token_actual() and self._token_actual()['token'] == 'PC':
                self._avanzar()

    def _parsear_llamada_funcion(self):
        func_tok = self._avanzar()
        if self._token_actual() and self._token_actual()['token'] == 'PAREN':
            self._avanzar()

        func = func_tok['token']
        arg_tok = self._token_actual()

        if func in ('LEERDIG', 'LEERCAD'):
            if arg_tok and arg_tok['token'] == 'id':
                self._avanzar()
                nombre = arg_tok['lexema']
                if nombre not in self.variables:
                    self._error(arg_tok['renglon'], arg_tok['columna'],
                                f"Variable no declarada: {nombre}",
                                "Variable no declarada", "desconocido")
                else:
                    tipo_esperado = 'ent' if func == 'LEERDIG' else 'cad'
                    if self.variables[nombre] != tipo_esperado:
                        self._error(arg_tok['renglon'], arg_tok['columna'],
                                    f"Error de tipo: se esperaba variable de tipo "
                                    f"'{tipo_esperado}', pero '{nombre}' es de tipo "
                                    f"'{self.variables[nombre]}'",
                                    "Error de tipo en lectura",
                                    f"se esperaba '{tipo_esperado}', "
                                    f"se obtuvo '{self.variables[nombre]}'")
            else:
                self._parsear_expresion()
        else:
            tipo_arg = self._parsear_expresion()
            if func == 'IMPCAD' and tipo_arg is not None and tipo_arg != 'cad':
                self._error(arg_tok['renglon'], arg_tok['columna'],
                            f"Error de tipo: se esperaba expresion de tipo 'cad', "
                            f"se obtuvo '{tipo_arg}'",
                            "Error de tipo en impresion",
                            f"se esperaba 'cad', se obtuvo '{tipo_arg}'")

        if self._token_actual() and self._token_actual()['token'] == 'TESIS':
            self._avanzar()
        if self._token_actual() and self._token_actual()['token'] == 'PC':
            self._avanzar()

    def _parsear_condicional(self):
        si_tok = self._avanzar()
        tipo_cond = self._parsear_expresion()
        if tipo_cond is not None and tipo_cond != 'bool':
            self._error(si_tok['renglon'], si_tok['columna'],
                        f"La condicion del 'si' debe ser de tipo bool, "
                        f"se obtuvo '{tipo_cond}'",
                        "Error de tipo en condicional",
                        f"se esperaba 'bool', se obtuvo '{tipo_cond}'")

        if self._token_actual() and self._token_actual()['token'] == 'ENTONCES':
            self._avanzar()

        while self._token_actual() and self._token_actual()['token'] not in ('SINO', 'FINSI'):
            self._parsear_sentencia()

        if self._token_actual() and self._token_actual()['token'] == 'SINO':
            self._avanzar()
            while self._token_actual() and self._token_actual()['token'] != 'FINSI':
                self._parsear_sentencia()

        if self._token_actual() and self._token_actual()['token'] == 'FINSI':
            self._avanzar()
        if self._token_actual() and self._token_actual()['token'] == 'PC':
            self._avanzar()

    def _parsear_bucle(self):
        mientras_tok = self._avanzar()
        tipo_cond = self._parsear_expresion()
        if tipo_cond is not None and tipo_cond != 'bool':
            self._error(mientras_tok['renglon'], mientras_tok['columna'],
                        f"La condicion del 'mientras' debe ser de tipo bool, "
                        f"se obtuvo '{tipo_cond}'",
                        "Error de tipo en bucle",
                        f"se esperaba 'bool', se obtuvo '{tipo_cond}'")

        if self._token_actual() and self._token_actual()['token'] == 'HACER':
            self._avanzar()

        while self._token_actual() and self._token_actual()['token'] != 'FINMIENTRAS':
            self._parsear_sentencia()

        if self._token_actual() and self._token_actual()['token'] == 'FINMIENTRAS':
            self._avanzar()
        if self._token_actual() and self._token_actual()['token'] == 'PC':
            self._avanzar()

    # =====================================================================
    # EXPRESIONES - analisis de tipos con precedencia
    # =====================================================================

    def _parsear_expresion(self):
        return self._parsear_or()

    def _parsear_or(self):
        tipo_izq = self._parsear_and()
        while self._token_actual() and self._token_actual()['token'] == 'O':
            op_tok = self._avanzar()
            tipo_der = self._parsear_and()
            if tipo_izq is not None and tipo_der is not None:
                if tipo_izq != 'bool' or tipo_der != 'bool':
                    self._error(op_tok['renglon'], op_tok['columna'],
                                "Error de tipo: operador 'o' requiere operandos de tipo bool",
                                "Error de tipo en expresion",
                                f"se esperaba 'bool'/'bool', se obtuvo "
                                f"'{tipo_izq}'/'{tipo_der}'")
                    tipo_izq = None
                else:
                    self.pila_semantica.append(tipo_izq)
                    self.pila_semantica.append(tipo_der)
                    self.pila_semantica.pop()
                    self.pila_semantica.pop()
                    tipo_izq = 'bool'
            else:
                tipo_izq = None
        return tipo_izq

    def _parsear_and(self):
        tipo_izq = self._parsear_not()
        while self._token_actual() and self._token_actual()['token'] == 'Y':
            op_tok = self._avanzar()
            tipo_der = self._parsear_not()
            if tipo_izq is not None and tipo_der is not None:
                if tipo_izq != 'bool' or tipo_der != 'bool':
                    self._error(op_tok['renglon'], op_tok['columna'],
                                "Error de tipo: operador 'y' requiere operandos de tipo bool",
                                "Error de tipo en expresion",
                                f"se esperaba 'bool'/'bool', se obtuvo "
                                f"'{tipo_izq}'/'{tipo_der}'")
                    tipo_izq = None
                else:
                    self.pila_semantica.append(tipo_izq)
                    self.pila_semantica.append(tipo_der)
                    self.pila_semantica.pop()
                    self.pila_semantica.pop()
                    tipo_izq = 'bool'
            else:
                tipo_izq = None
        return tipo_izq

    def _parsear_not(self):
        if self._token_actual() and self._token_actual()['token'] == 'NO':
            op_tok = self._avanzar()
            tipo = self._parsear_relacional()
            if tipo is not None and tipo != 'bool':
                self._error(op_tok['renglon'], op_tok['columna'],
                            "Error de tipo: operador 'no' requiere operando de tipo bool",
                            "Error de tipo en expresion",
                            f"se esperaba 'bool', se obtuvo '{tipo}'")
                return None
            self.pila_semantica.append(tipo)
            self.pila_semantica.pop()
            return 'bool'
        return self._parsear_relacional()

    def _parsear_relacional(self):
        tipo_izq = self._parsear_adicion()
        if self._token_actual() and self._token_actual()['token'] in (
                'EQU', 'DIF', 'MAYOR', 'MENOR', 'MAYIG', 'MENIG'):
            op_tok = self._avanzar()
            tipo_der = self._parsear_adicion()
            op = op_tok['token']
            if tipo_izq is not None and tipo_der is not None:
                if op in ('EQU', 'DIF'):
                    if tipo_izq != tipo_der:
                        self._error(op_tok['renglon'], op_tok['columna'],
                                    f"Error de tipo: operador '{op_tok['lexema']}' "
                                    f"requiere operandos del mismo tipo",
                                    "Error de tipo en expresion",
                                    f"se esperaba mismo tipo, se obtuvo "
                                    f"'{tipo_izq}'/'{tipo_der}'")
                        return None
                else:
                    if tipo_izq != 'ent' or tipo_der != 'ent':
                        self._error(op_tok['renglon'], op_tok['columna'],
                                    f"Error de tipo: operador '{op_tok['lexema']}' "
                                    f"requiere operandos de tipo ent",
                                    "Error de tipo en expresion",
                                    f"se esperaba 'ent'/'ent', se obtuvo "
                                    f"'{tipo_izq}'/'{tipo_der}'")
                        return None
                self.pila_semantica.append(tipo_izq)
                self.pila_semantica.append(tipo_der)
                self.pila_semantica.pop()
                self.pila_semantica.pop()
                return 'bool'
            return None
        return tipo_izq

    def _parsear_adicion(self):
        tipo_izq = self._parsear_multiplicacion()
        while self._token_actual() and self._token_actual()['token'] in ('MAS', 'MENOS'):
            op_tok = self._avanzar()
            tipo_der = self._parsear_multiplicacion()
            if tipo_izq is not None and tipo_der is not None:
                if tipo_izq != 'ent' or tipo_der != 'ent':
                    self._error(op_tok['renglon'], op_tok['columna'],
                                f"Error de tipo: operador '{op_tok['lexema']}' "
                                f"requiere operandos de tipo ent",
                                "Error de tipo en expresion",
                                f"se esperaba 'ent'/'ent', se obtuvo "
                                f"'{tipo_izq}'/'{tipo_der}'")
                    tipo_izq = None
                else:
                    self.pila_semantica.append(tipo_izq)
                    self.pila_semantica.append(tipo_der)
                    self.pila_semantica.pop()
                    self.pila_semantica.pop()
                    tipo_izq = 'ent'
            else:
                tipo_izq = None
        return tipo_izq

    def _parsear_multiplicacion(self):
        tipo_izq = self._parsear_unario()
        while self._token_actual() and self._token_actual()['token'] in ('MUL', 'DIV'):
            op_tok = self._avanzar()
            tipo_der = self._parsear_unario()
            if tipo_izq is not None and tipo_der is not None:
                if tipo_izq != 'ent' or tipo_der != 'ent':
                    self._error(op_tok['renglon'], op_tok['columna'],
                                f"Error de tipo: operador '{op_tok['lexema']}' "
                                f"requiere operandos de tipo ent",
                                "Error de tipo en expresion",
                                f"se esperaba 'ent'/'ent', se obtuvo "
                                f"'{tipo_izq}'/'{tipo_der}'")
                    tipo_izq = None
                else:
                    self.pila_semantica.append(tipo_izq)
                    self.pila_semantica.append(tipo_der)
                    self.pila_semantica.pop()
                    self.pila_semantica.pop()
                    tipo_izq = 'ent'
            else:
                tipo_izq = None
        return tipo_izq

    def _parsear_unario(self):
        if self._token_actual() and self._token_actual()['token'] == 'MENOS':
            op_tok = self._avanzar()
            tipo = self._parsear_unario()
            if tipo is not None and tipo != 'ent':
                self._error(op_tok['renglon'], op_tok['columna'],
                            "Error de tipo: operador '-' unario requiere operando de tipo ent",
                            "Error de tipo en expresion",
                            f"se esperaba 'ent', se obtuvo '{tipo}'")
                return None
            self.pila_semantica.append(tipo)
            self.pila_semantica.pop()
            return 'ent'
        return self._parsear_primario()

    def _parsear_primario(self):
        tok = self._token_actual()
        if not tok:
            return None

        if tok['token'] == 'CENT':
            self._avanzar()
            self.pila_semantica.append('ent')
            return 'ent'

        if tok['token'] == 'CAD_LIT':
            self._avanzar()
            self.pila_semantica.append('cad')
            return 'cad'

        if tok['token'] in ('VERDADERO', 'FALSO'):
            self._avanzar()
            self.pila_semantica.append('bool')
            return 'bool'

        if tok['token'] == 'id':
            self._avanzar()
            nombre = tok['lexema']
            if nombre not in self.variables:
                self._error(tok['renglon'], tok['columna'],
                            f"Variable no declarada: {nombre}",
                            "Variable no declarada", "desconocido")
                return None
            tipo = self.variables[nombre]
            self.pila_semantica.append(tipo)
            return tipo

        if tok['token'] == 'PAREN':
            self._avanzar()
            tipo = self._parsear_expresion()
            if self._token_actual() and self._token_actual()['token'] == 'TESIS':
                self._avanzar()
            return tipo

        return None

    # =====================================================================
    # GENERACION DEL ARCHIVO DE SALIDA .sem
    # =====================================================================

    def generar_sem(self, ruta_salida):
        with open(ruta_salida, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("     ANALISIS SEMANTICO - ANALIZADOR LEXICO PF2025\n")
            f.write("=" * 70 + "\n\n")

            f.write("--- VARIABLES DECLARADAS ---\n")
            f.write("-" * 70 + "\n")
            for nombre, tipo in self.variables.items():
                f.write(f"Variable: {nombre:<20} Tipo: {tipo}\n")
            f.write(f"Total de variables declaradas: {len(self.variables)}\n\n")

            errores = _errores_unificados(self.errores_lexicos, self.errores)
            f.write("--- ERRORES ---\n")
            f.write("-" * 70 + "\n")
            if errores:
                for err in errores:
                    f.write(f"Renglon: {err['renglon']}, Columna: {err['columna']}, "
                            f"{err['fase']}, Tipo de dato: {err['tipo_dato']}, "
                            f"{err['descripcion']}\n")
            else:
                f.write("No se encontraron errores.\n")

            f.write("\n" + "=" * 70 + "\n")
            f.write(f"Total de errores: {len(errores)}\n")
        print(f"[OK] Analisis semantico generado: {ruta_salida}")


# ===========================================================================
# ERRORES UNIFICADOS (lexicos y semanticos)
# ===========================================================================
def _errores_unificados(errores_lexicos, errores_semanticos):
    """
    Combina los errores lexicos y semanticos en una sola lista
    ordenada por renglon y columna.
    Cada error conserva: renglon, columna, fase, tipo de dato
    y descripcion.
    """
    unificados = [
        {'renglon': e['linea'], 'columna': e.get('columna', 0),
         'fase': 'Lexico', 'tipo_dato': '-',
         'descripcion': e['descripcion']}
        for e in errores_lexicos
    ]
    unificados += [
        {'renglon': e['renglon'], 'columna': e['columna'],
         'fase': 'Semantico', 'tipo_dato': e.get('tipo_dato', '-'),
         'descripcion': e['descripcion']}
        for e in errores_semanticos
    ]
    unificados.sort(key=lambda e: (e['renglon'], e['columna']))
    return unificados


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
            print(f"Renglon: {err['renglon']}, Columna: {err['columna']}, "
                  f"{err['fase']}, Tipo de dato: {err['tipo_dato']}, "
                  f"{err['descripcion']}")
    else:
        print("No se encontraron errores.")
    print("=" * 70)

    print("\n" + "=" * 70)
    print("    PROCESO COMPLETADO EXITOSAMENTE")
    print(f"    Archivos generados en: {carpeta_salida}")
    print(f"    Total de errores: {len(errores)}")
    print("=" * 70)


if __name__ == "__main__":
    main()
