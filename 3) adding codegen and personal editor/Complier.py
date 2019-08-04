from rply import LexerGenerator, ParserGenerator
from llvmlite import ir, binding
import subprocess
import random
import string
def randomString2(stringLength=8):
    """Generate a random string of fixed length """
    letters= string.ascii_lowercase
    return ''.join(random.sample(letters,stringLength))

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
        self.lexer.add('WQ', r'\"')
        # Operators
        self.lexer.add('SUM', r'\+')
        self.lexer.add('SUB', r'\-')
        self.lexer.add('MUP', r'\*')
        self.lexer.add('DIV', r'\/')
        
        self.lexer.add('EQUAL', r'=')

        self.lexer.add('GREATER',  r'\>')
        self.lexer.add('SMALLER',  r'\<')
        self.lexer.add('NOT', r'\!')
        # semi colon
        self.lexer.add('SEMI_COLON', r'\;')
        
        #logical
        self.lexer.add('AND', r'and')
        self.lexer.add('OR' , r'or' )

        # colon
        self.lexer.add('COLON', r'\:')
        # comma
        self.lexer.add('COMMA',',')
        
        # Number
        self.lexer.add('NUMBER', r'\d+')
        #String
        self.lexer.add('STRING',r'\w*')
        # Variables
        # right now all the alphabets written here <a n d o r i f e l s :> will not be accecpted
        #AND if  i replace round brackets with square then if else will not work
        self.lexer.add('VAR', r'[^(and)|(or)|(if)|(else)|(:) ]\w*')
       
        # Ignore spaces
        self.lexer.ignore('\s+')
        
        #if else
        self.lexer.add('IF', r'if')
        self.lexer.add('ELSE', r'else')

    def get_lexer(self):
        self._add_tokens()
        return self.lexer.build()

###########################################
#ast
class Number():
    def __init__(self, builder, module, value):
        self.builder = builder
        self.module = module
        self.value = value

    def eval(self):
        i = ir.Constant(ir.IntType(8), int(self.value))
        return i
class String():
    def __init__(self, builder, module, value):
        self.builder = builder
        self.module = module
        self.value = value

    def eval(self):
        i = ir.Constant(ir.IntType(8), str(self.value))
        return i

class BinaryOp():
    def __init__(self, builder, module, left, right):
        self.builder = builder
        self.module = module
        self.left = left
        self.right = right


class Sum(BinaryOp):
    def eval(self):
        i = self.builder.add(self.left.eval(), self.right.eval())
        return i

class Sub(BinaryOp):
    def eval(self):
        i = self.builder.sub(self.left.eval(), self.right.eval())
        return i

class Mup(BinaryOp):
    def eval(self):
        i = self.builder.mul(self.left.eval(), self.right.eval())
        return i

class Div(BinaryOp):
    def eval(self):
        i = self.builder.sdiv(self.left.eval(), self.right.eval())
        return i

class Greater(BinaryOp):
    def eval(self):
        i = self.builder.icmp_signed('>',self.left.eval(), self.right.eval())
        return i

class Smaller(BinaryOp):
    def eval(self):
        i = self.builder.icmp_signed('<',self.left.eval(), self.right.eval())
        return i

class EEqual(BinaryOp):
    def eval(self):
        i = self.builder.icmp_signed('==',self.left.eval(), self.right.eval())
        return i

class GEqual(BinaryOp):
    def eval(self):
        i = self.builder.icmp_signed('>=',self.left.eval(), self.right.eval())
        return i

class LEqual(BinaryOp):
    def eval(self):
        i = self.builder.icmp_signed('<=',self.left.eval(), self.right.eval())
        return i

class NEqual(BinaryOp):
    def eval(self):
        i = self.builder.icmp_signed('!=',self.left.eval(), self.right.eval())
        return i

class And(BinaryOp):
    def eval(self):
        i = self.builder.and_(self.left.eval(), self.right.eval())
        return i

class Or(BinaryOp):
    def eval(self):
        i = self.builder.or_(self.left.eval(), self.right.eval())
        return i

class Print():
    def __init__(self, builder, module, printf, value):
        self.builder = builder
        self.module = module
        self.printf = printf
        self.value = value

    def eval(self):
        value = self.value.eval()
        
        # Declare argument list
        voidptr_ty = ir.IntType(8).as_pointer() 

        fmt = "\n%i\0"
        
        c_fmt = ir.Constant(ir.ArrayType (ir.IntType(8), len(fmt)) , bytearray(fmt.encode("latin1")))
        global_fmt = ir.GlobalVariable(self.module, c_fmt.type, name=randomString2(random.randint(2,5)))

        global_fmt.linkage = 'internal'
        global_fmt.global_constant = True
        global_fmt.initializer = c_fmt

        fmt_arg = self.builder.bitcast(global_fmt, voidptr_ty)

        # Call Print Function
        self.builder.call(self.printf, [fmt_arg, value])

def fun(a,b):
    d={ }
    d[str( a.value )] = b.eval()
    name.update(d)

#parser
        
class Parser():
    def __init__(self, module, builder, printf):
        self.pg = ParserGenerator(
            # A list of all token names accepted by the parser.
            ['NUMBER', 'PRINT','IF', 'ELSE', 'OPEN_PAREN', 'CLOSE_PAREN',
             'SUM', 'SUB', 'MUP', 'DIV','EQUAL','COMMA','STRING','WQ',
             'GREATER', 'SMALLER','NOT','AND','OR','COLON',
             'VAR'],

            precedence= [
                ('left', ['SUM','SUB']),
                ('left', ['MUP','DIV']),
                ('left', ['GREATER','SMALLER']),
                ('right',['NOT']),
                ('right', ['EQUAL']),
                ('left', ['AND','OR']),
                ('left',['COMMA'])
                        ]
                                )
        self.module = module
        self.builder = builder
        self.printf = printf

        
    def parse(self):
        
        @self.pg.production('program : PRINT OPEN_PAREN expression CLOSE_PAREN COMMA program')
        def print_program(p):
            Print(self.builder, self.module, self.printf, p[2]).eval()

        @self.pg.production('program : PRINT OPEN_PAREN expression CLOSE_PAREN ')
        def print_program(p):
            Print(self.builder, self.module, self.printf, p[2]).eval()

        
        @self.pg.production('program : VAR EQUAL expression')                           
        def statment(p):
            d={ }
            d[str( p[0].value )] = p[2].eval()
            name.update(d)

        @self.pg.production('program : VAR EQUAL expression COMMA program')                           
        def statment(p):
            d={ }
            d[str( p[0].value )] = p[2].eval()
            name.update(d)

        @self.pg.production('program : IF expression COLON if_else_expression ELSE COLON if_else_expression ')         
        def if_else_program(p):                                                                            
            if str(p[1].eval()) == 'True':                                                                  
                try:
                    fun(p[3][0],p[3][1])
                except:
                    Print(self.builder, self.module, self.printf, p[3]).eval()
                
            elif str(p[1].eval()) == 'False':
                try:
                    fun(p[6][0],p[6][1])
                except:
                    Print(self.builder, self.module, self.printf, p[6]).eval()

        @self.pg.production('program : VAR')                                             
        def statement_var(p):
            print(name[ str( p[0].value ) ])                                                   

        @self.pg.production('program : VAR COMMA program')                                             
        def statement_var(p):
            print(name[ str( p[0].value ) ])

        @self.pg.production('program : expression')
        def statement_expr(p):
            return Print(self.builder, self.module, self.printf, p[0]).eval()

        @self.pg.production('if_else_expression : PRINT OPEN_PAREN expression CLOSE_PAREN')
        def print_program(p):
            return p[2]                                                   
                                                                                          
        @self.pg.production('if_else_expression : VAR EQUAL expression')
        def statment(p):
            return p[0],p[2]

        @self.pg.production('expression : expression GREATER expression')
        @self.pg.production('expression : expression SMALLER expression')
        def expression_artm(p):
            if p[1].gettokentype() == 'GREATER':
                return Greater(self.builder, self.module, p[0], p[2])
            elif p[1].gettokentype() == 'SMALLER':
                return Smaller(self.builder, self.module, p[0], p[2])

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
                return Sum(self.builder, self.module,p[0], p[2])
            elif p[1].gettokentype() == 'SUB':
                return Sub(self.builder, self.module,p[0], p[2])
            elif p[1].gettokentype() == 'MUP':
                return Mup(self.builder, self.module,p[0], p[2])
            elif p[1].gettokentype() == 'DIV':
                return Div(self.builder, self.module,p[0], p[2])
            elif p[1].gettokentype() ==     'EQUAL'   and p[2].gettokentype() == 'EQUAL':
                return EEqual(self.builder, self.module,p[0], p[3])
            elif p[1].gettokentype() ==     'GREATER' and p[2].gettokentype() == 'EQUAL':
                return GEqual(self.builder, self.module,p[0], p[3])
            elif p[1].gettokentype() ==     'SMALLER' and p[2].gettokentype() == 'EQUAL':
                return LEqual(self.builder, self.module,p[0], p[3])
            elif p[1].gettokentype() ==     'NOT'     and p[2].gettokentype() == 'EQUAL':
                return NEqual(self.builder, self.module,p[0], p[3])

        @self.pg.production('expression : OPEN_PAREN expression CLOSE_PAREN')
        def expression_group(p):
            return p[1]

        @self.pg.production('expression : NUMBER')
        def number(p):
            return Number(self.builder, self.module, p[0].value)
        @self.pg.production('expression : WQ STRING WQ')
        def number(p):
            return String(self.builder, self.module, p[1].value)

        @self.pg.production('expression : expression AND expression')
        @self.pg.production('expression : expression OR  expression')
        def expr_logic(p):
            if p[1].gettokentype() == 'AND':
                return And(self.builder, self.module,p[0], p[2])
            elif p[1].gettokentype() == 'OR':
                return Or(self.builder, self.module,p[0], p[2])

        @self.pg.error
        def error_handle(token):
            raise ValueError(token)

    def get_parser(self):
        return self.pg.build()

#codegen
class CodeGen():
    def __init__(self):
        self.binding = binding 
        self.binding.initialize() 
        self.binding.initialize_native_target() 
        self.binding.initialize_native_asmprinter() 
        
        self._config_llvm() 
        self.engine = self._create_execution_engine()
        self._declare_print_function()

    def _config_llvm(self):
        # Config LLVM
        self.module = ir.Module(name='xyz')
        self.module.triple = self.binding.get_default_triple()
        func_type = ir.FunctionType(ir.VoidType(), [], False)
        base_func = ir.Function(self.module, func_type, name="main")
        block = base_func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(block)

    def _create_execution_engine(self):
        """
        Create an ExecutionEngine suitable for JIT code generation on
        the host CPU.  The engine is reusable for an arbitrary number of
        modules.
        """ 
        target = self.binding.Target.from_default_triple()
        target_machine = target.create_target_machine()
        # And an execution engine with an empty backing module
        backing_mod = binding.parse_assembly("")
        engine = binding.create_mcjit_compiler(backing_mod, target_machine)
        return engine

    def _declare_print_function(self):
        # Declare Printf function
        voidptr_ty = ir.IntType(8).as_pointer()
        printf_ty = ir.FunctionType(ir.IntType(8), [voidptr_ty], var_arg=True)
        printf = ir.Function(self.module, printf_ty, name="printf")
        self.printf = printf

    def _compile_ir(self):
        """
        Compile the LLVM IR string with the given engine.
        The compiled module object is returned.
        """
        # Create a LLVM module object from the IR
        self.builder.ret_void()
        llvm_ir = str(self.module)
        mod = self.binding.parse_assembly(llvm_ir)
        mod.verify() 
        # Now add the module and make sure it is ready for execution
        self.engine.add_module(mod)
        self.engine.finalize_object()
        self.engine.run_static_constructors()
        return mod



    def create_ir(self):
        self._compile_ir()

    def save_ir(self):
        return str(self.module)
