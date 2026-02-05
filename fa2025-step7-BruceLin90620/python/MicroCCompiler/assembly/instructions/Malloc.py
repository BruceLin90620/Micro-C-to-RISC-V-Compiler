from .Instruction import Instruction, OpCode

class Malloc(Instruction):
  def __init__(self, src: str, dest: str):
    super().__init__()
    self.src = src
    self.dest = dest
    self.oc = OpCode.MALLOC

  def __str__(self):
    return str(self.oc) + " " + self.dest + ", " + self.src
