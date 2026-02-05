from abc import ABC, abstractmethod
from .Instruction import Instruction

class InstructionPut(Instruction):
  def __init__(self, src: str):
    super().__init__()
    self.src1 = src

  def __str__(self):
    return str(self.oc) + " " + self.src1
