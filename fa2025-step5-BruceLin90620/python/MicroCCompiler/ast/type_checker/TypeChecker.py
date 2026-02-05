from ..visitor.AbstractASTVisitor import AbstractASTVisitor
from ..BinaryOpNode import BinaryOpNode
from ..UnaryOpNode import UnaryOpNode
from ..CallNode import CallNode
from ..CondNode import CondNode
from ..AssignNode import AssignNode
from ..ReturnNode import ReturnNode
from ...compiler.Scope import Scope
from typing import Any
from .. import *

class MicroCTypeError(Exception):
    pass

class TypeChecker(AbstractASTVisitor):
    def run(self, node: 'ASTNode') -> Any:
        return super().run(node)

    def error(self):
        raise MicroCTypeError()

    def _check_op_type(self, left_type, right_type=None):
        if left_type in [Scope.Type.STRING, Scope.Type.VOID]:
            self.error()

        if right_type is not None:
            if left_type != right_type:
                self.error()

    def postprocessBinaryOpNode(self, node:BinaryOpNode, left: Any, right: Any) -> Any:
        left_type = node.getLeft().getType()
        right_type = node.getRight().getType()
        self._check_op_type(left_type, right_type)
        return None

    def postprocessUnaryOpNode(self, node: UnaryOpNode, expr: Any) -> Any:
        expr_type = node.getExpr().getType()
        self._check_op_type(expr_type, None)
        return None
    
    def postprocessAssignNode(self, node: AssignNode, left: Any, right: Any) -> Any:
        left_type = node.getLeft().getType()
        right_type = node.getRight().getType()

        if left_type != right_type:
            self.error()

        return None
    
    def postprocessCondNode(self, node: CondNode, left: Any, right: Any) -> Any:
        left_type = node.getLeft().getType()
        right_type = node.getRight().getType()
        self._check_op_type(left_type, right_type)
        return None

    def postprocessCallNode(self, node: CallNode, args: Any) -> Any:
        func_ste = node.ste
        if func_ste is None:
            self.error()
        expected_arg_types = func_ste.getArgTypes()
        actual_args = node.getArgs()

        if len(expected_arg_types) != len(actual_args):
            self.error()

        for idx, (expected_type, actual_arg_node) in enumerate(zip(expected_arg_types, actual_args)):
            actual_type = actual_arg_node.getType()
            if expected_type != actual_type:
                self.error()

        return None

    def postprocessReturnNode(self, node: ReturnNode, retExpr: Any) -> Any:
        func_return_type = node.getFuncSymbol().getReturnType()
        expr_type = node.getRetExpr().getType()

        if func_return_type != expr_type:
            self.error()

        return None
    