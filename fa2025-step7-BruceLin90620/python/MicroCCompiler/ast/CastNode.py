from .ASTNode import ASTNode
from typing import TYPE_CHECKING, Any
from ..compiler.Scope import Scope

if TYPE_CHECKING:
  from .visitor import ASTVisitor

class CastNode(ASTNode):
  def __init__(self, type: Scope.Type, expr: ASTNode):
    self.setCastType(type)
    self.setExpr(expr)
    self.setType(type)

  def accept(self, visitor: 'ASTVisitor') -> Any:
    return visitor.visitCastNode(self)

  def getExpr(self) -> ASTNode:
    return self.expr

  def setExpr(self, expr: ASTNode):
    self.expr = expr

  def getCastType(self) -> Scope.Type:
    return self.castType

  def setCastType(self, type: Scope.Type):
    self.castType = type