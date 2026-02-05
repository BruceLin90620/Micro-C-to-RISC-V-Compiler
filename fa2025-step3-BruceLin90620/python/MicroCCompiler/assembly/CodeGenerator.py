import sys
import os

from .CodeObject import CodeObject
from .InstructionList import InstructionList
from .instructions import *
from ..compiler import *
from ..ast import *
from ..ast.visitor.AbstractASTVisitor import AbstractASTVisitor

class CodeGenerator(AbstractASTVisitor):

  def __init__(self):
    self.intRegCount = 0
    self.floatRegCount = 0
    self.intTempPrefix = 't'
    self.floatTempPrefix = 'f'
    self.loopLabel = 0
    self.elseLabel = 0
    self.outLabel = 0

  def getIntRegCount(self):
    return self.intRegCount

  def getFloatRegCount(self):
    return self.floatRegCount

  # Generate code for Variables
  #
  # Create a code object that just holds a variable
  # Important: add a pointer from the code object to the symbol table entry so
  # we know how to generate code for it later (we'll need it to find the
  # address)
  #
  # Mark the code object as holding a variable, and also as an lval

  def postprocessVarNode(self, node: VarNode) -> CodeObject:
    sym = node.getSymbol()

    co = CodeObject(sym)
    co.lval = True
    co.type = node.getType()

    return co

  # Generate code for IntLiterals
  #
  # Use load immediate instruction to do this
  
  def postprocessIntLitNode(self, node: IntLitNode) -> CodeObject:
    co = CodeObject()
    i = Li(self.generateTemp(Scope.Type.INT), node.getVal())
		
    #Load an immediate into a register
		#The li and la instructions are the same, but it's helpful to distinguish
		#for readability purposes.
		#li tmp' value

    co.code.append(i) #add this instruction to the code object
    co.lval = False #co holds an rval -- data
    co.temp = i.getDest()
    co.type = node.getType() # temp is in destination of li
    return co

  # Generate code for FloatLiterals
  #
  # Use load immediate instruction to do this

  def postprocessFloatLitNode(self, node: FloatLitNode) -> CodeObject:
    co = CodeObject()

    #Load an immediate into a register
		#The li and la instructions are the same, but it's helpful to distinguish
		#for readability purposes.
		#li tmp' value
    i = FImm(self.generateTemp(Scope.Type.FLOAT), node.getVal())
    
    co.code.append(i) # add this instruction to the code object
    co.lval = False # co holds an rval -- data
    co.temp = i.getDest() # temp is in destination of li
    co.type = node.getType()
    return co

	 # Generate code for binary operations.
	 # 
	 # Step 0: create new code object
	 # Step 1: add code from left child
	 # Step 1a: if left child is an lval, add a load to get the data
	 # Step 2: add code from right child
	 # Step 2a: if right child is an lval, add a load to get the data
	 # Step 3: generate binary operation using temps from left and right
	 # 
	 # Don't forget to update the temp and lval fields of the code object!
	 # 	   Hint: where is the result stored? Is this data or an address?

  def postprocessBinaryOpNode(self, node: BinaryOpNode, left: CodeObject, right: CodeObject) -> CodeObject:
    co = CodeObject()
    #FILL CODE FOR STEP 2
    if left.lval is True:
      left = self.rvalify(left)
    co.code.extend(left.code)

    if right.lval is True:
      right = self.rvalify(right)
    co.code.extend(right.code)   

    op = node.getOp()
    typ = node.getType()
    new_temp = self.generateTemp(typ)
    inst = None

    if op == BinaryOpNode.OpType.ADD:
      if typ == Scope.Type.INT:
        inst = Add(left.temp, right.temp, new_temp)
      elif typ == Scope.Type.FLOAT:
        inst = FAdd(left.temp, right.temp, new_temp)
      else:
        raise Exception("Unary minus on unsupported type")

    elif op == BinaryOpNode.OpType.SUB:
      if typ == Scope.Type.INT:
        inst = Sub(left.temp, right.temp, new_temp)
      elif typ == Scope.Type.FLOAT:
        inst = FSub(left.temp, right.temp, new_temp)
      else:
        raise Exception("Unary minus on unsupported type")
      
    elif op == BinaryOpNode.OpType.MUL:
      if typ == Scope.Type.INT:
        inst = Mul(left.temp, right.temp, new_temp)
      elif typ == Scope.Type.FLOAT:
        inst = FMul(left.temp, right.temp, new_temp)
      else:
        raise Exception("Unary minus on unsupported type")
      
    elif op == BinaryOpNode.OpType.DIV:
      if typ == Scope.Type.INT:
        inst = Div(left.temp, right.temp, new_temp)
      elif typ == Scope.Type.FLOAT:
        inst = FDiv(left.temp, right.temp, new_temp)
      else:
        raise Exception("Unary minus on unsupported type")
      
    else:
      raise Exception("Invalid opcode in BinaryOp")

    co.code.append(inst)
    co.lval = False
    co.temp = new_temp
    co.type = typ

    return co
	 
   #  Generate code for unary operations.
	 #  
	 #  Step 0: create new code object
	 #  Step 1: add code from child expression
	 #  Step 1a: if child is an lval, add a load to get the data
	 #  Step 2: generate instruction to perform unary operation (don't forget to generate right type of op)
	 #  
	 #  Don't forget to update the temp and lval fields of the code object!
	 #  	   Hint: where is the result stored? Is this data or an address?
	  
  def postprocessUnaryOpNode(self, node: UnaryOpNode, expr: CodeObject) -> CodeObject:
    co = CodeObject()
    #FILL IN CODE FOR STEP 2
    if expr.lval is True:
      expr = self.rvalify(expr)
    co.code.extend(expr.code)

    op = node.getOp()
    typ = node.getType()
    new_temp = self.generateTemp(typ)
    inst = None
    if op == UnaryOpNode.OpType.NEG:
      if typ == Scope.Type.INT:
        inst = Neg(expr.temp, new_temp)
      elif typ == Scope.Type.FLOAT:
        inst = FNeg(expr.temp, new_temp)
      else:
        raise Exception("Unary minus on unsupported type")

    co.code.append(inst)
    co.lval = False
    co.temp = new_temp
    co.type = typ

    return co

	 # Generate code for assignment statements
	 # 
	 # Step 0: create new code object
	 # Step 1a: if LHS is a variable, generate a load instruction to get the address into a register
	 #          (see generateAddrFromVariable)
	 # Step 1b: add code from LHS of assignment (make sure it results in an lval!)
	 # Step 2: add code from RHS of assignment
	 # Step 2a: if right child is an lval, add a load to get the data
	 # Step 3: generate store (don't forget to generate the right type of store)
	 # 
	 # Hint: it is going to be easiest to just generate a store with a 0 immediate
	 # offset, and the complete store address in a register:
	 # 
	 # sw rhs 0(lhs)

  def postprocessAssignNode(self, node: AssignNode, left: CodeObject, right: CodeObject) -> CodeObject:
    co = CodeObject()
    assert(left.lval is True)

    #Step 1a
    if left.isVar():
      left = self.generateAddrFromVariable(left)
    #FILL IN CODE FOR STEP 2
    co.code.extend(left.code)

    if right.lval is True:
      right = self.rvalify(right)
    co.code.extend(right.code)

    typ = node.getType()
    inst = None

    if typ == Scope.Type.INT:
      inst = Sw(right.temp, left.temp, "0")
    elif typ == Scope.Type.FLOAT:
      inst = Fsw(right.temp, left.temp, "0")
    else:
      raise Exception("Shouldn't read into other variable")
    
    co.code.append(inst)
    co.lval = False #doesn't matter
    co.temp = None #set to None to trigger errors
    co.type = None #set to None to trigger errors

    return co

  # Add together all the lists of instructions generated by the children

  def postprocessStatementListNode(self, node: StatementListNode, statements: list) -> CodeObject:
    co = CodeObject()

    for subcode in statements:
      co.code.extend(subcode.code)

    co.type = None
    return co

	 # Generate code for read
	 # 
	 # Step 0: create new code object
	 # Step 1: add code from VarNode (make sure it's an lval)
	 # Step 2: generate GetI instruction, storing into temp
	 # Step 3: generate store, to store temp in variable
	
  def postprocessReadNode(self, node: ReadNode, var: CodeObject) -> CodeObject:
    co = CodeObject()
    assert(var.getSTE() is not None)
    tmp = self.generateAddrFromVariable(var)

    co.code.extend(tmp.code)

    il = InstructionList()

    typ = node.getType()

    if typ == Scope.Type.INT:
 		  # Code to generate if INT:
			#	geti tmp
			#	sw tmp 0(var.tmp)
      geti = GetI(self.generateTemp(Scope.Type.INT))
      il.append(geti)
      sw = Sw(geti.getDest(), tmp.temp, "0")
      il.append(sw)
    elif typ == Scope.Type.FLOAT:
      # Code to generate if FLOAT:
			#	getf tmp
			#	fsw tmp 0(var.tmp)
      getf = GetF(self.generateTemp(Scope.Type.FLOAT))
      il.append(getf)
      fsw = Fsw(getf.getDest(), tmp.temp, "0")
      il.append(fsw)
    else:
      raise Exception("Shouldn't read into other variable")

    co.code.extend(il)

    co.lval = False #doesn't matter
    co.temp = None #set to None to trigger errors
    co.type = None #set to None to trigger errors

    return co
	 
   # Generate code for print
	 # 
	 # Step 0: create new code object
	 # 
	 # If printing a string:
	 # Step 1: add code from expression to be printed (make sure it's an lval)
	 # Step 2: generate a PutS instruction printing the result of the expression
	 # 
	 # If printing an integer:
	 # Step 1: add code from the expression to be printed
	 # Step 1a: if it's an lval, generate a load to get the data
	 # Step 2: Generate PutI that prints the temporary holding the expression

  def postprocessWriteNode(self, node: WriteNode, expr: CodeObject) -> CodeObject:
    co = CodeObject()
    #generating code for write(expr)

    #for strings, we expect a variable
    if node.getWriteExpr().getType() == Scope.Type.STRING:
      #Step 1:
      assert(expr.getSTE() is not None)

      #Get the address of the variable
      addrCo = self.generateAddrFromVariable(expr)
      co.code.extend(addrCo.code)

      #Step 2:
      write = PutS(addrCo.temp)
      co.code.append(write)
    else:
      #Step 1a:
      #if expr is an lval, load from it
      if expr.lval is True:
        expr = self.rvalify(expr)

      #Step 1:
      co.code.extend(expr.code)

      #Step 2:
      #if type of writenode is int, use puti, if float, use putf
      write = None
      typ = node.getWriteExpr().getType()
      if typ == Scope.Type.STRING:
        raise Exception("Shouldn't have a STRING here")
      elif typ == Scope.Type.INT:
        write = PutI(expr.temp)
      elif typ == Scope.Type.FLOAT:
        write = PutF(expr.temp)
      else:
        raise Exception("WriteNode has a weird type")
      co.code.append(write)

    co.lval = False #doesn't matter
    co.temp = None #set to None to trigger errors
    co.type = None #set to None to trigger errors
    return co

	#  Generating an instruction sequence for a conditional expression
	#  
	#  Implement this however you like. One suggestion:
	# 
	#  Create the code for the left and right side of the conditional, but defer
	#  generating the branch until you process IfStatementNode or WhileNode (since you
	#  do not know the labels yet). Modify CodeObject so you can save the necessary
	#  information to generate the branch instruction in IfStatementNode or WhileNode
	#  
	#  Alternate idea 1:
	#  
	#  Don't do anything as part of CodeGenerator. Create a new visitor class
	#  that you invoke *within* your processing of IfStatementNode or WhileNode
	#  
	#  Alternate idea 2:
	#  
	#  Create the branch instruction in this function, then tweak it as necessary in
	#  IfStatementNode or WhileNode
	#  
	#  Hint: you may need to preserve extra information in the returned CodeObject to
	#  make sure you know the type of branch code to generate (int vs float)

  def postprocessCondNode(self, node: CondNode, left: CodeObject, right: CodeObject) -> CodeObject:
    print(f"DEBUG postprocessCondNode: left.type={left.getType()}, right.type={right.getType()}, op={node.getOp()}")
    co = CodeObject()
    #FILL IN CODE FOR STEP 3
    if left.lval is True:
      left = self.rvalify(left)
    co.code.extend(left.code)
    if right.lval is True:
      right = self.rvalify(right)
    co.code.extend(right.code)

    co.temp = (left.temp, right.temp, node.getOp(), left.getType())
    print(f"DEBUG postprocessCondNode: co.temp={co.temp}")
    co.lval = False
    co.type = None
    return co

   # Code generation for IfStatement
	 # Step 0: Create code object
	 # 
	 # Step 1: generate labels
	 # 
	 # Step 2: add code from conditional expression
	 # 
	 # Step 3: create branch statement (if not created as part of step 2)
	 # 			don't forget to generate correct branch based on type
	 # 
	 # Step 4: generate code
	 # 		<cond code>
	 #		<flipped branch> elseLabel
	 #		<then code>
	 #		j outLabel
	 #		elseLabel:
	 #		<else code>
	 #		outLabel:
	 #
	 # Step 5 insert code into code object in appropriate order.

  def postprocessIfStatementNode(self, node: IfStatementNode, cond: CodeObject, tlist: CodeObject, elist: CodeObject) -> CodeObject:
    co = CodeObject()
    #FILL IN CODE FOR STEP 3
    print("DEBUG: IfStatementNode")
    elseLabel = self.generateElseLabel()
    outLabel = self.generateOutLabel()
    left_temp, right_temp, op, operandType = cond.getTemp()

    if operandType == Scope.Type.INT:
        if op == CondNode.OpType.LT:
            branch_inst = Bge(left_temp, right_temp, elseLabel)
        elif op == CondNode.OpType.LE:
            branch_inst = Bgt(left_temp, right_temp, elseLabel)
        elif op == CondNode.OpType.GT:
            branch_inst = Ble(left_temp, right_temp, elseLabel)
        elif op == CondNode.OpType.GE:
            branch_inst = Blt(left_temp, right_temp, elseLabel)
        elif op == CondNode.OpType.EQ:
            branch_inst = Bne(left_temp, right_temp, elseLabel)
        elif op == CondNode.OpType.NE:
            branch_inst = Beq(left_temp, right_temp, elseLabel)
        
        co.code.extend(cond.code)
        co.code.append(branch_inst)

    elif operandType == Scope.Type.FLOAT:
        result_reg = self.generateTemp(Scope.Type.INT)
        co.code.extend(cond.code)
        
        if op == CondNode.OpType.LT:
            co.code.append(Flt(left_temp, right_temp, result_reg))  # Fixed order!
            co.code.append(Beq(result_reg, "x0", elseLabel))
        elif op == CondNode.OpType.LE:
            co.code.append(Fle(left_temp, right_temp, result_reg))  # Fixed order!
            co.code.append(Beq(result_reg, "x0", elseLabel))
        elif op == CondNode.OpType.GT:
            co.code.append(Flt(right_temp, left_temp, result_reg))  # Fixed order!
            co.code.append(Beq(result_reg, "x0", elseLabel))
        elif op == CondNode.OpType.GE:
            co.code.append(Fle(right_temp, left_temp, result_reg))  # Fixed order!
            co.code.append(Beq(result_reg, "x0", elseLabel))
        elif op == CondNode.OpType.EQ:
            co.code.append(Feq(left_temp, right_temp, result_reg))  # Fixed order!
            co.code.append(Beq(result_reg, "x0", elseLabel))
        elif op == CondNode.OpType.NE:
            co.code.append(Feq(left_temp, right_temp, result_reg))  # Fixed order!
            co.code.append(Bne(result_reg, "x0", elseLabel))
    else:
        raise Exception("Bad cond type")
    

    co.code.extend(tlist.code)
    co.code.append(J(outLabel))
    co.code.append(elseLabel + ":")
    if elist is not None:
      co.code.extend(elist.code)
    co.code.append(outLabel + ":")
    return co

   # Code generation for While statement
	 # Step 0: Create code object
	 # 
	 # Step 1: generate labels
	 # 
	 # Step 2: add code from conditional expression
	 # 
	 # Step 3: create branch statement (if not created as part of step 2)
	 # 			don't forget to generate correct branch based on type
	 # 
	 # Step 4: generate code
	 # 		loopLabel:
	 #		<cond code>
	 #		<flipped branch> outLabel
	 #		<body code>
	 #		j loopLabel
	 #		outLabel:
	 #
	 # Step 5 insert code into code object in appropriate order.

  def postprocessWhileNode(self, node: WhileNode, cond: CodeObject, wlist: CodeObject) -> CodeObject:
    co = CodeObject()
    #FILL IN CODE FOR STEP 3
    print("DEBUG: WhileNode")
    loopLabel = self.generateLoopLabel()
    outLabel = self.generateOutLabel()
    left_temp, right_temp, op, operandType= cond.getTemp()

    co.code.append(loopLabel + ":")

    if operandType == Scope.Type.INT:
        if op == CondNode.OpType.LT:
            branch_inst = Bge(left_temp, right_temp, outLabel)
        elif op == CondNode.OpType.LE:
            branch_inst = Bgt(left_temp, right_temp, outLabel)
        elif op == CondNode.OpType.GT:
            branch_inst = Ble(left_temp, right_temp, outLabel)
        elif op == CondNode.OpType.GE:
            branch_inst = Blt(left_temp, right_temp, outLabel)
        elif op == CondNode.OpType.EQ:
            branch_inst = Bne(left_temp, right_temp, outLabel)
        elif op == CondNode.OpType.NE:
            branch_inst = Beq(left_temp, right_temp, outLabel)
        
        co.code.extend(cond.code)
        co.code.append(branch_inst)

    elif operandType == Scope.Type.FLOAT:
      result_reg = self.generateTemp(Scope.Type.INT)
      
      co.code.extend(cond.code)
      
      if op == CondNode.OpType.LT:
          co.code.append(Flt(left_temp, right_temp, result_reg))  # Fixed!
          co.code.append(Beq(result_reg, "x0", outLabel))
      elif op == CondNode.OpType.LE:
          co.code.append(Fle(left_temp, right_temp, result_reg))  # Fixed!
          co.code.append(Beq(result_reg, "x0", outLabel))
      elif op == CondNode.OpType.GT:
          co.code.append(Flt(right_temp, left_temp, result_reg))  # Fixed!
          co.code.append(Beq(result_reg, "x0", outLabel))
      elif op == CondNode.OpType.GE:
          co.code.append(Fle(right_temp, left_temp, result_reg))  # Fixed!
          co.code.append(Beq(result_reg, "x0", outLabel))
      elif op == CondNode.OpType.EQ:
          co.code.append(Feq(left_temp, right_temp, result_reg))  # Fixed!
          co.code.append(Beq(result_reg, "x0", outLabel))
      elif op == CondNode.OpType.NE:
          co.code.append(Feq(left_temp, right_temp, result_reg))  # Fixed!
          co.code.append(Bne(result_reg, "x0", outLabel))
    else:
        raise Exception("Bad cond type")
    
    
    co.code.extend(wlist.code)
    co.code.append(J(loopLabel))
    co.code.append(outLabel + ":")

    return co

  # Generating code for returns
	# 
	# For now, we don't do anything with return values, so just generate HALT
  
  def postprocessReturnNode(self, node: ReturnNode, retExpr: CodeObject) -> CodeObject:
    co = CodeObject()

    #if retexpr is an lval, load from it
    if retExpr.lval is True:
      retExpr = self.rvalify(retExpr)

    co.code.extend(retExpr.code)

    #We don't support functions yet, so a return is just a halt
    h = Halt()
    co.code.append(h)
    co.type = None #set to None to trigger errors

    return co

	# Generate a fresh temporary
	# 
	# @return new temporary register name
  
  def generateTemp(self, t: Scope.Type) -> str:
    if t == Scope.Type.INT:
      s = self.intTempPrefix + str(self.intRegCount)
      self.intRegCount += 1
      return s
    elif t == Scope.Type.FLOAT:
      s = self.floatTempPrefix + str(self.floatRegCount)
      self.floatRegCount += 1
      return s
    else:
      raise Exception("Generating temp for bad type")

  def generateLoopLabel(self) -> str:
    self.loopLabel += 1
    return "loop_" + str(self.loopLabel)

  def generateElseLabel(self) -> str:
    self.elseLabel += 1
    return "else_" + str(self.elseLabel)

  def generateOutLabel(self) -> str:
    self.outLabel += 1
    return "out_" + str(self.outLabel)

	 # Take a code object that results in an lval, and create a new code
	 # object that adds a load to generate the rval.
	 # 
	 # Step 0: Create new code object
	 # 
	 # Step 1: Add all the lco code to the new code object
	 # 		   (If lco is just a variable, create a new code object that
	 #          stores the address of variable in a code object; see
	 #          generateAddrFromVariable)
	 # 
	 # Step 2: Generate a load to load from lco's temp into a new temporary
	 # 		   Hint: it'll be easiest to generate a load with no offset:
	 # 				lw newtemp 0(oldtemp)
	 #         Don't forget to generate the right kind of load based on the type
	 #         stored in the address
	 # 
	 # Don't forget to update the temp and lval fields of the code object!
	 # 		   Hint: where is the result stored? Is this data or an address?
	 # 
	 # @param lco The code object resulting in an address
	 # @return A code object with all the code of <code>lco</code> followed by a load
	 #         to generate an rval

  def rvalify(self, lco : CodeObject) -> CodeObject:
    # Step 0
    co = CodeObject()
    assert(lco.lval is True)
    # FILL IN CODE FOR STEP 2
    if lco.isVar():
      lco = self.generateAddrFromVariable(lco)

    co.code.extend(lco.code)
    
    typ = lco.getType()
    new_temp = self.generateTemp(typ)
    if typ == Scope.Type.INT:
      inst = Lw(new_temp, lco.temp, "0")
    elif typ == Scope.Type.FLOAT:
      inst = Flw(new_temp, lco.temp, "0")
    else:
      raise Exception("Shouldn't rvalify into other variable")

    co.code.append(inst)

    co.lval = False
    co.temp = new_temp
    co.type = typ

    return co


	# Take a code object that holds just a variable and turn it into a code object
	# that places the address of that variable into a registers
	# 
	# @param lco The code object holding a variable
	# @return A code object with the variable's address in a register

  def generateAddrFromVariable(self, lco: CodeObject) -> CodeObject:
    co = CodeObject()

    #Step 1:
    symbol = lco.getSTE()
    address = str(symbol.getAddress())

    #Step 2:
    #la tmp' addr // Register type needs to be an int
    loadAddr = La(self.generateTemp(Scope.Type.INT), address)
    
    co.code.append(loadAddr) #add instruction to code object
    co.lval = True #co holds an lval, because it's an address
    co.temp = loadAddr.getDest() #temp is in destination of la
    co.ste = None #not a variable
    co.type = symbol.getType() #even though register type is an int, address points to Type

    return co
