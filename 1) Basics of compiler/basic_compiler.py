from rply import LexerGenerator
from rply import ParserGenerator
from llvmlite import ir, binding
from ctypes import CFUNCTYPE,c_int8

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
        # Number
        self.lexer.add('NUMBER', r'\d+')
        # Ignore spaces
        self.lexer.ignore('\s+')

    def get_lexer(self):
        self._add_tokens()
        return self.lexer.build()


#ast
class Number():
    def __init__(self, builder, module, value):
        self.builder = builder
        self.module = module
        self.value = value

    def eval(self):
        i = ir.Constant(ir.IntType(8), int(self.value))
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
        
        fmt = "%i \n\0" 
        
        c_fmt = ir.Constant(ir.ArrayType (ir.IntType(8), len(fmt)) , bytearray(fmt.encode("latin1"))) 
        global_fmt = ir.GlobalVariable(self.module, c_fmt.type, name="fstr")

        global_fmt.linkage = 'internal'
        global_fmt.global_constant = True
        global_fmt.initializer = c_fmt

        fmt_arg = self.builder.bitcast(global_fmt, voidptr_ty)

        # Call Print Function
        self.builder.call(self.printf, [fmt_arg, value])

#parser
class Parser():
    def __init__(self, module, builder, printf):
        self.pg = ParserGenerator(
            # A list of all token names accepted by the parser.
            ['NUMBER', 'PRINT', 'OPEN_PAREN', 'CLOSE_PAREN',
             'SUM', 'SUB'],

            precedence= [
                ('left', ['SUM','SUB']),
                ('left', ['MUP','DIV'])]
        )
        
        self.module = module
        self.builder = builder
        self.printf = printf

    def parse(self):
        @self.pg.production('program : PRINT OPEN_PAREN expression CLOSE_PAREN')
        def program(p):
            return Print(self.builder, self.module, self.printf, p[2])

        @self.pg.production('expression : expression SUM expression')
        @self.pg.production('expression : expression SUB expression')
        def expression(p):
            left = p[0]
            right = p[2]
            operator = p[1]
            if operator.gettokentype() == 'SUM':
                return Sum(self.builder, self.module, left, right)
            elif operator.gettokentype() == 'SUB':
                return Sub(self.builder, self.module, left, right)

        @self.pg.production('expression : NUMBER')
        def number(p):
            return Number(self.builder, self.module, p[0].value)

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
        self.engine, self.tg = self._create_execution_engine() 
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
        return engine , target_machine 

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
        with open('final.o','wb') as o:
            o.write(self.tg.emit_object(mod))
            
        return mod 

    def create_ir(self):
        self._compile_ir()
        # y = self._compile_ir()
        # return y

    def save_ir(self, filename):
        with open(filename, 'w') as output_file:
            output_file.write(str(self.module))
    def show_op(self):
        print(self.module)
        

#main
text_input = input("##>")

lexer = Lexer().get_lexer()
tokens = lexer.lex(text_input)

codegen = CodeGen()

module = codegen.module
builder = codegen.builder
printf = codegen.printf

pg = Parser(module, builder, printf)
pg.parse()
parser = pg.get_parser()
parser.parse(tokens).eval()
codegen.create_ir()
codegen.save_ir("output.ll")

