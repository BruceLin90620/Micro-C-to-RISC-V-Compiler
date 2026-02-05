from .AbstractASTVisitor import AbstractASTVisitor
from .. import * # 匯入所有 AST 節點類型
from ...compiler.Scope import Scope
from typing import Any

class ASTPrintVisitor(AbstractASTVisitor):
    def __init__(self, indent_level=0):
        self.indent_level = indent_level

    def _indent(self):
        return "  " * self.indent_level

    def _visit_child(self, node):
        if node is None:
            return f"{self._indent()}  None\n"
        visitor = ASTPrintVisitor(self.indent_level + 1)
        return node.accept(visitor)

    def visitVarNode(self, node: 'VarNode') -> str:
        return f"{self._indent()}VarNode(ident: {node.getIdent()}, type: {node.getType()})\n"

    def visitIntLitNode(self, node: 'IntLitNode') -> str:
        return f"{self._indent()}IntLitNode(val: {node.getVal()}, type: {node.getType()})\n"

    def visitFloatLitNode(self, node: 'FloatLitNode') -> str:
        return f"{self._indent()}FloatLitNode(val: {node.getVal()}, type: {node.getType()})\n"

    def visitBinaryOpNode(self, node: 'BinaryOpNode') -> str:
        s = f"{self._indent()}BinaryOpNode(op: {node.getOp().name}, type: {node.getType()})\n"
        s += self._visit_child(node.getLeft())
        s += self._visit_child(node.getRight())
        return s

    def visitUnaryOpNode(self, node: 'UnaryOpNode') -> str:
        s = f"{self._indent()}UnaryOpNode(op: {node.getOp().name}, type: {node.getType()})\n"
        s += self._visit_child(node.getExpr())
        return s

    def visitAssignNode(self, node: 'AssignNode') -> str:
        s = f"{self._indent()}AssignNode(type: {node.getType()})\n"
        s += f"{self._indent()}- LValue:\n"
        s += self._visit_child(node.getLeft())
        s += f"{self._indent()}- RValue:\n"
        s += self._visit_child(node.getRight())
        return s

    def visitStatementListNode(self, node: 'StatementListNode') -> str:
        s = f"{self._indent()}StatementListNode\n"
        for i, stmt in enumerate(node.getStatements()):
            s += f"{self._indent()}- Stmt[{i}]:\n"
            s += self._visit_child(stmt)
        return s

    def visitReadNode(self, node: 'ReadNode') -> str:
        s = f"{self._indent()}ReadNode\n"
        s += self._visit_child(node.getVarNode())
        return s

    def visitWriteNode(self, node: 'WriteNode') -> str:
        s = f"{self._indent()}WriteNode\n"
        s += self._visit_child(node.getWriteExpr())
        return s

    def visitIfStatementNode(self, node: 'IfStatementNode') -> str:
        s = f"{self._indent()}IfStatementNode\n"
        s += f"{self._indent()}- Condition:\n"
        s += self._visit_child(node.getCondExpr())
        s += f"{self._indent()}- Then Block:\n"
        s += self._visit_child(node.getThenBlock())
        if node.getElseBlock():
            s += f"{self._indent()}- Else Block:\n"
            s += self._visit_child(node.getElseBlock())
        return s

    def visitWhileNode(self, node: 'WhileNode') -> str:
        s = f"{self._indent()}WhileNode\n"
        s += f"{self._indent()}- Condition:\n"
        s += self._visit_child(node.getCondExpr())
        s += f"{self._indent()}- Body:\n"
        s += self._visit_child(node.getSList())
        return s

    def visitReturnNode(self, node: 'ReturnNode') -> str:
        s = f"{self._indent()}ReturnNode\n"
        s += self._visit_child(node.getRetExpr())
        return s

    def visitCondNode(self, node: 'CondNode') -> str:
        s = f"{self._indent()}CondNode(op: {node.getOp().name})\n"
        s += self._visit_child(node.getLeft())
        s += self._visit_child(node.getRight())
        return s

    def visitFunctionNode(self, node: 'FunctionNode') -> str:
        s = f"{self._indent()}FunctionNode(name: {node.getFuncName()})\n"
        s += f"{self._indent()}- Body:\n"
        s += self._visit_child(node.getFuncBody())
        return s

    def visitFunctionListNode(self, node: 'FunctionListNode') -> str:
        s = f"{self._indent()}FunctionListNode\n"
        for func in node.getFunctions():
            s += self._visit_child(func)
        return s

    def visitCallNode(self, node: 'CallNode') -> str:
        s = f"{self._indent()}CallNode(name: {node.getFuncName()}, type: {node.getType()})\n"
        s += f"{self._indent()}- Args:\n"
        for i, arg in enumerate(node.getArgs()):
            s += f"{self._indent()}- Arg[{i}]:\n"
            s += self._visit_child(arg)
        return s

    def postprocessVarNode(self, node: 'VarNode') -> Any: return self.visitVarNode(node)
    def postprocessIntLitNode(self, node: 'IntLitNode') -> Any: return self.visitIntLitNode(node)
    def postprocessFloatLitNode(self, node: 'FloatLitNode') -> Any: return self.visitFloatLitNode(node)
    def postprocessBinaryOpNode(self, node: 'BinaryOpNode', left: Any, right: Any) -> Any: return self.visitBinaryOpNode(node)
    def postprocessUnaryOpNode(self, node: 'UnaryOpNode', expr: Any) -> Any: return self.visitUnaryOpNode(node)
    def postprocessAssignNode(self, node: 'AssignNode', left: Any, right: Any) -> Any: return self.visitAssignNode(node)
    def postprocessStatementListNode(self, node: 'StatementListNode', statements: list) -> Any: return self.visitStatementListNode(node)
    def postprocessReadNode(self, node: 'ReadNode', var: Any) -> Any: return self.visitReadNode(node)
    def postprocessWriteNode(self, node: 'WriteNode', writeExpr: Any) -> Any: return self.visitWriteNode(node)
    def postprocessIfStatementNode(self, node: 'IfStatementNode', cond: Any, tlist: Any, elist: Any) -> Any: return self.visitIfStatementNode(node)
    def postprocessWhileNode(self, node: 'WhileNode', cond: Any, slist: Any) -> Any: return self.visitWhileNode(node)
    def postprocessReturnNode(self, node: 'ReturnNode', retExpr: Any) -> Any: return self.visitReturnNode(node)
    def postprocessCondNode(self, node: 'CondNode', left: Any, right: Any) -> Any: return self.visitCondNode(node)
    def postprocessFunctionNode(self, node: 'FunctionNode', body: Any) -> Any: return self.visitFunctionNode(node)
    def postprocessFunctionListNode(self, node: 'FunctionListNode', functions: Any) -> Any: return self.visitFunctionListNode(node)
    def postprocessCallNode(self, node: 'CallNode', args: Any) -> Any: return self.visitCallNode(node)