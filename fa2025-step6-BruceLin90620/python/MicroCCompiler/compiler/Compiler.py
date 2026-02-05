import sys

from antlr4 import FileStream, CommonTokenStream
from antlr4.error.ErrorStrategy import DefaultErrorStrategy

from MicroCLexer import MicroCLexer
from MicroCParser import MicroCParser

from .Scope import Scope
from .SymbolTable import StaticVariables, SymbolTable
from ..ast.ASTNode import ASTNode
from ..assembly.CodeGenerator import CodeGenerator
from ..assembly.CodeObject import CodeObject
from ..ast.type_checker.TypeChecker import TypeChecker
from ..ast.type_checker.TypeChecker import MicroCTypeError
from ..ast.visitor.ASTPrintVisitor import ASTPrintVisitor

class MyErrorStrategy(DefaultErrorStrategy):
    def reportError(self, _recognizer, _exception):
        print("Not Accepted")
        exit(1)
    def recoverInline(self, _recognizer):
        print("Not Accepted")
        exit(1)

def printStrings(st: SymbolTable):
  g = st.getGlobalScope()
  stes = g.getEntries()

  print("\n.section .strings")

  for ste in stes:
    if ste.getType().type == Scope.InnerType.STRING:
      print("{} {}".format(hex(int(ste.getAddress())), ste.getValue()))

def main(filename):
    try:
        input_stream = FileStream(filename)
        lexer = MicroCLexer(input_stream)
        
        token_stream = CommonTokenStream(lexer)
        parser = MicroCParser(token_stream)
        
        parser._errHandler = MyErrorStrategy()
        
        parser.setSymbolTable(StaticVariables.getSymbolTableSingleton())
        
        _parse_tree = parser.program()
        
        parser.getSymbolTable().printTable()

        ast = parser.getAST()

        # type_checker = TypeChecker()
        # type_checker.run(ast)

        # print("\n--- Abstract Syntax Tree ---", file=sys.stderr)
        # printer = ASTPrintVisitor()
        # ast_string = printer.run(ast)
        # print(ast_string, file=sys.stderr)
        # print("------------------------------\n", file=sys.stderr)

        cg = CodeGenerator()
        co = cg.run(ast)

        print(".section .text")
        print(co)
        printStrings(parser.getSymbolTable())

    except FileNotFoundError:
        print("File not found")
        return 1
    return 0
    
if __name__ == "__main__":
    exit(main())
