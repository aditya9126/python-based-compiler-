from rply import LexerGenerator, ParserGenerator

name = { }

#lexer
class Lexer():
    def __init__(self):
        self.lexer = LexerGenerator()

    def _add_tokens(self):
        # Print
        self.lexer.add('PRINT', r'print')
                                                                                    
        # Parenthesis
        self.lexer.add('OPEN_PAREN', r'\(')
        self.lexer.add('CLOSE_PAREN', r'\)')

        # Operators
        self.lexer.add('SUM', r'\+')
        self.lexer.add('SUB', r'\-')
        self.lexer.add('MUP', r'\*')
        self.lexer.add('DIV', r'\/')
        
        self.lexer.add('EQUAL', r'=')

        self.lexer.add('GREATER',  r'\>')
        self.lexer.add('SMALLER',  r'\<')
        self.lexer.add('NOT', r'\!')

        #logical
        self.lexer.add('AND', r'and')
        self.lexer.add('OR' , r'or' )

        # colon
        self.lexer.add('COLON', r'\:')
        
        # Number
        self.lexer.add('NUMBER', r'\d+')

        # Variables
        self.lexer.add('VAR', r'[^and|or|if|else|: ]\w*')

        # Ignore spaces
        self.lexer.ignore('\s+')
        
        #if else
        self.lexer.add('IF', r'if')
        self.lexer.add('ELSE', r'else')

    def get_lexer(self):
        self._add_tokens()
        return self.lexer.build()

#ast

class Number():
    def __init__(self, value):
        self.value = value

    def eval(self):
        return int(self.value)

class BinaryOp():
    def __init__(self, left, right):
        self.left = left
        self.right = right

class Sum(BinaryOp):
    def eval(self):
        return self.left.eval() + self.right.eval()

class Sub(BinaryOp):
    def eval(self):
        return self.left.eval() - self.right.eval()

class Mup(BinaryOp):
    def eval(self):
        return self.left.eval() * self.right.eval()

class Div(BinaryOp):
    def eval(self):
        return self.left.eval() / self.right.eval()

class Greater(BinaryOp):
    def eval(self):
        return self.left.eval() > self.right.eval()

class Smaller(BinaryOp):
    def eval(self):
        return self.left.eval() < self.right.eval()

class EEqual(BinaryOp):
    def eval(self):
        return self.left.eval() == self.right.eval()

class GEqual(BinaryOp):
    def eval(self):
        return self.left.eval() >= self.right.eval()

class LEqual(BinaryOp):
    def eval(self):
        return self.left.eval() <= self.right.eval()

class NEqual(BinaryOp):
    def eval(self):
        return self.left.eval() != self.right.eval()

class And(BinaryOp):
    def eval(self):
        return self.left.eval() and self.right.eval()

class Or(BinaryOp):
    def eval(self):
        return self.left.eval() or self.right.eval()

class Print():
    def __init__(self, value):
        self.value = value

    def eval(self):
        print((self.value.eval()))

def fun(a,b):
    d={ }
    d[str( a )] = b.eval()
    name.update(d)

#parser  
class Parser():
    def __init__(self):
        self.pg = ParserGenerator(
            # A list of all token names accepted by the parser.
            ['NUMBER', 'PRINT','IF', 'ELSE', 'OPEN_PAREN', 'CLOSE_PAREN',
             'SUM', 'SUB', 'MUP', 'DIV','EQUAL',
             'GREATER', 'SMALLER','NOT','AND','OR','COLON',
             'VAR'],

            precedence= [
                ('left', ['SUM','SUB']),
                ('left', ['MUP','DIV']),
                ('left', ['GREATER','SMALLER']),
                ('right',['NOT']),
                ('right', ['EQUAL']),
                ('left', ['AND','OR'])
                        ]
                                )

    def parse(self):
        
        @self.pg.production('program : PRINT OPEN_PAREN expression CLOSE_PAREN')
        def print_program(p):
            return Print(p[2]).eval()                                                  
                                     
        @self.pg.production('program : VAR EQUAL expression')                           
        def statment(p):
            d={ }
            d[str( p[0] )] = p[2].eval()
            name.update(d)

        @self.pg.production('program : IF expression COLON expression ELSE COLON expression ')         
        def if_else_program(p):                                                                            
            if str(p[1].eval()) == 'True':                                                                  
                try:
                    fun(p[3][0],p[3][1])
                except:
                    Print(p[3]).eval()
                
            elif str(p[1].eval()) == 'False':
                try:
                    fun(p[6][0],p[6][1])
                except:
                    Print(p[6]).eval()

        @self.pg.production('program : VAR')                                             
        def statement_var(p):
            print(name[ str( p[0] ) ])                                                   

        @self.pg.production('program : expression')
        def statement_expr(p):
            return Print(p[0]).eval()

        @self.pg.production('expression : expression GREATER expression')
        @self.pg.production('expression : expression SMALLER expression')
        def expression_artm(p):
            if p[1].gettokentype() == 'GREATER':
                return Greater(p[0], p[2])
            elif p[1].gettokentype() == 'SMALLER':
                return Smaller(p[0], p[2])

        @self.pg.production('expression : expression SUM     expression')
        @self.pg.production('expression : expression SUB     expression')
        @self.pg.production('expression : expression MUP     expression')
        @self.pg.production('expression : expression DIV     expression')
        @self.pg.production('expression : expression EQUAL   EQUAL  expression')
        @self.pg.production('expression : expression GREATER EQUAL  expression')
        @self.pg.production('expression : expression SMALLER EQUAL  expression')
        @self.pg.production('expression : expression NOT     EQUAL  expression')
        def expression_artm(p):
            if p[1].gettokentype() ==   'SUM':
                return Sum(p[0], p[2])
            elif p[1].gettokentype() == 'SUB':
                return Sub(p[0], p[2])
            elif p[1].gettokentype() == 'MUP':
                return Mup(p[0], p[2])
            elif p[1].gettokentype() == 'DIV':
                return Div(p[0], p[2])
            elif p[1].gettokentype() ==     'EQUAL'   and p[2].gettokentype() == 'EQUAL':
                return EEqual(p[0], p[3])
            elif p[1].gettokentype() ==     'GREATER' and p[2].gettokentype() == 'EQUAL':
                return GEqual(p[0], p[3])
            elif p[1].gettokentype() ==     'SMALLER' and p[2].gettokentype() == 'EQUAL':
                return LEqual(p[0], p[3])
            elif p[1].gettokentype() ==     'NOT'     and p[2].gettokentype() == 'EQUAL':
                return NEqual(p[0], p[3])

        @self.pg.production('expression : OPEN_PAREN expression CLOSE_PAREN')
        def expression_group(p):
            return p[1]

        @self.pg.production('expression : NUMBER')
        def number(p):
            return Number(p[0].value)

        @self.pg.production('expression : expression AND expression')
        @self.pg.production('expression : expression OR  expression')
        def expr_logic(p):
            if p[1].gettokentype() == 'AND':
                return And(p[0], p[2])
            elif p[1].gettokentype() == 'OR':
                return Or(p[0], p[2])


        @self.pg.production('expression : PRINT OPEN_PAREN expression CLOSE_PAREN')
        def print_program(p):
            return p[2]                                                    
                                                                                          
        @self.pg.production('expression : VAR EQUAL expression')
        def statment(p):
            return p[0],p[2]

        @self.pg.error
        def error_handle(token):
            raise ValueError(token)

    def get_parser(self):
        return self.pg.build()

#main

while True:
    try:
        text_input = input('@@@')

        lexer = Lexer().get_lexer()
        tokens = lexer.lex(text_input)

    except EOFError:
        break

    pg = Parser()
    pg.parse()
    parser = pg.get_parser()    
    parser.parse(tokens)
