"""Pruebas de aceptacion de la rubrica; nunca modifican entrada/progfte.txt."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

RAIZ = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('analizador', RAIZ / 'src/analizador_lexico.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def analizar(texto):
    lexico = m.AnalizadorLexico('memoria')
    lexico.lineas_originales = texto.splitlines(True)
    with contextlib.redirect_stdout(io.StringIO()):
        lexico.depurar_codigo()
        lexico.analizar()
        sem = m.AnalizadorSemantico(lexico.lista_tokens, lexico.errores)
        sem.analizar()
    return lexico, sem, m._errores_unificados(lexico.errores, sem.errores)


class Rubrica(unittest.TestCase):
    def programa(self, cuerpo, declaraciones='Ent a; Bool b; cad c;'):
        return analizar(f'pf2025 prueba\ndecl\n{declaraciones}\ninicio\n{cuerpo}\nfin')

    def test_referencia(self):
        lex, sem, errores = analizar((RAIZ / 'entrada/progfte.txt').read_text(encoding='utf-8'))
        self.assertEqual((len(lex.lista_tokens), len(lex.tabla_simbolos), len(sem.variables)), (273,61,5))
        self.assertEqual([(e['renglon'],e['fase']) for e in errores], [(5,'Lexico'),(65,'Semantico'),(67,'Semantico')])
        self.assertTrue(sem.ast_sentencias)
        self.assertEqual(sem.pila_semantica, [])

    def test_no_declarada(self):
        for cuerpo in ['x := 1;', 'a := x;', 'impdig(x);', 'impBool(x);']:
            with self.subTest(cuerpo=cuerpo):
                self.assertEqual(self.programa(cuerpo)[2][0]['tipo_error'], 'Variable no declarada')

    def test_duplicada(self):
        _, sem, errores = self.programa('', 'Ent a; Bool a;')
        self.assertEqual(len(errores), 1)
        self.assertEqual((errores[0]['tipo_esperado'],errores[0]['tipo_obtenido']), ('ent','bool'))
        self.assertEqual(sem.variables['a'], 'ent')

    def test_asignaciones(self):
        for cuerpo in ['a := verdadero;', 'b := 1;', 'c := falso;']:
            with self.subTest(cuerpo=cuerpo):
                self.assertEqual(self.programa(cuerpo)[2][0]['tipo_error'], 'Asignacion incompatible')

    def test_operadores_invalidos(self):
        for expr in ['1+verdadero','1-falso','"a"*2','1/verdadero','1 y falso',
                     'verdadero o 1','no 1','-falso','1==falso','1!=falso','"x">1',
                     'falso<1','verdadero>=1','1<=falso']:
            with self.subTest(expr=expr):
                errores=self.programa(f'impdig({expr});')[2]
                self.assertEqual(len(errores),1)
                self.assertEqual(errores[0]['tipo_error'],'Operandos incompatibles')

    def test_precedencia_ast_pila(self):
        _, sem, errores=self.programa('a := 1+2*3; b := no no falso o a>0 y verdadero;')
        self.assertEqual(errores,[])
        expr=sem.ast_sentencias[0]['expresion']
        self.assertEqual(expr['lexema'],'+')
        self.assertEqual(expr['hijos'][1]['lexema'],'*')
        self.assertEqual(sem.ast_sentencias[1]['expresion']['lexema'],'o')
        self.assertEqual(sem.pila_semantica,[])

    def test_condicional(self):
        errores=self.programa('si 1 entonces a := falso; sino c := 1; finsi;')[2]
        self.assertEqual([e['tipo_error'] for e in errores],
                         ['Condicion incompatible','Asignacion incompatible','Asignacion incompatible'])

    def test_bucle(self):
        errores=self.programa('mientras 1 hacer a := falso; finmientras;')[2]
        self.assertEqual([e['tipo_error'] for e in errores],['Condicion incompatible','Asignacion incompatible'])

    def test_anidamiento_ambito(self):
        _, sem, errores=self.programa('mientras a>0 hacer si b entonces a := a-1; sino mientras falso hacer a := 0; finmientras; finsi; finmientras;')
        self.assertEqual(errores,[])
        self.assertEqual(sem.ast_sentencias[0]['cuerpo'][0]['alternativo'][0]['clase'],'Mientras')
        self.assertTrue(all(s['ambito']=='global' for s in sem.tabla_simbolos.values()))

    def test_lecturas(self):
        for expr in ['1','a+1','(a)','verdadero','"x"']:
            with self.subTest(expr=expr):
                self.assertEqual(self.programa(f'leerdig({expr});')[2][0]['tipo_error'],'Argumento de lectura invalido')
        for cuerpo in ['leerdig(c);','leercad(a);']:
            self.assertEqual(self.programa(cuerpo)[2][0]['tipo_error'],'Tipo incompatible en lectura')
        self.assertEqual(self.programa('leerdig(a); leercad(c);')[2],[])

    def test_impresiones_excepciones(self):
        self.assertEqual(self.programa('impdig(verdadero); impBool(1); impcad(c);')[2],[])
        self.assertEqual(self.programa('impcad(1);')[2][0]['tipo_error'],'Tipo incompatible en impresion')

    def test_columnas_originales(self):
        _,_,errores=self.programa('    /* texto */ x := 1;')
        self.assertEqual((errores[0]['renglon'],errores[0]['columna']),(5,17))

    def test_cadenas_comentarios(self):
        lex,_,errores=self.programa('impcad("hola /*literal*/ ;, ) (  fin"); /* externo\ncontinua */')
        self.assertEqual(errores,[])
        self.assertIn('"hola /*literal*/ ;, ) (  fin"',[t['lexema'] for t in lex.lista_tokens])

    def test_comentario_abierto(self):
        _,_,errores=analizar('pf2025 p inicio fin /* abierto')
        self.assertEqual(len(errores),1)
        self.assertEqual(errores[0]['tipo_error'],'Comentario sin cierre')

    def test_lexemas_invalidos(self):
        for nombre in ['nombre@Usuario','mi_variable','_variable','123abc']:
            with self.subTest(nombre=nombre):
                lex,_,_=self.programa('',f'Ent {nombre};')
                self.assertEqual(len(lex.errores),1)

    def test_desigualdad_sin_espacios(self):
        self.assertEqual(self.programa('si a!=0 entonces a := 0; finsi;')[2],[])

    def test_recuperacion_sintaxis(self):
        for cuerpo in ['a := ;','leerdig();','a := (1+2;','si verdadero a := 1; finsi;',
                      'mientras verdadero hacer a := 1;', 'a := 1<2<3;', 'Ent local;']:
            with self.subTest(cuerpo=cuerpo):
                _,sem,errores=self.programa(cuerpo)
                self.assertTrue(any(e['fase']=='Sintactico' for e in errores))
                self.assertEqual(sem.pila_semantica,[])

    def test_propagar_error_sin_cascada(self):
        for expr in ['-x','no x','x+1']:
            with self.subTest(expr=expr):
                self.assertEqual(len(self.programa(f'impdig({expr});')[2]),1)

    def test_archivos(self):
        lex,sem,errores=self.programa('a := falso;')
        with tempfile.TemporaryDirectory() as tmp:
            tok=Path(tmp)/'p.tok'; salida=Path(tmp)/'p.sem'
            with contextlib.redirect_stdout(io.StringIO()):
                lex.generar_tok(tok,sem.errores);sem.generar_sem(str(salida))
            for archivo in [tok,salida]:
                contenido=archivo.read_text(encoding='utf-8')
                for campo in ['Renglon: 5','Columna: 1','Semantico','Tipo de error: Asignacion incompatible','esperado: ent; obtenido: bool']:
                    self.assertIn(campo,contenido)
            self.assertEqual(json.loads((Path(tmp)/'p.ast.json').read_text(encoding='utf-8')),sem.ast)


if __name__=='__main__':
    unittest.main()
