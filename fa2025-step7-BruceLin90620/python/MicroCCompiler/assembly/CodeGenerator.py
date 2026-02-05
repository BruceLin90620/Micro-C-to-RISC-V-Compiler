import sys
import os
from typing import List

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
    self.currFunc = None

  def getIntRegCount(self):
    return self.intRegCount

  def getFloatRegCount(self):
    return self.floatRegCount

  # to unpack the InnerType
  def _get_inner_type(self, t):
    if hasattr(t, 'type'):
        return t.type
    return t

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
    i = Li(self.generateTemp(Scope.InnerType.INT), node.getVal())
		
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
    i = FImm(self.generateTemp(Scope.InnerType.FLOAT), node.getVal())
    
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
    # Step 0: create new code object
    co = CodeObject()
    #FILL CODE FOR STEP 2

    # Step 1: add code from left child
    # Step 1a: if left child is an lval, add a load to get the data
    if left.lval is True:
      left = self.rvalify(left)
    co.code.extend(left.code)

    # Step 2: add code from right child
    # Step 2a: if right child is an lval, add a load to get the data
    if right.lval is True:
      right = self.rvalify(right)
    co.code.extend(right.code)   

	  # Step 3: generate binary operation using temps from left and right
    op = node.getOp()
    typ = node.getType()
    inner_type = self._get_inner_type(typ) # FIX: extract inner type
    
    new_temp = self.generateTemp(inner_type)
    inst = None

    # For arithmetic, treat PTR like INT
    if op == BinaryOpNode.OpType.ADD:
      if inner_type == Scope.InnerType.INT or inner_type == Scope.InnerType.PTR:
        inst = Add(left.temp, right.temp, new_temp)
      elif inner_type == Scope.InnerType.FLOAT:
        inst = FAdd(left.temp, right.temp, new_temp)
      else:
        raise TypeError(f"Type mismatch for {op.name}")

    elif op == BinaryOpNode.OpType.SUB:
      if inner_type == Scope.InnerType.INT or inner_type == Scope.InnerType.PTR:
        inst = Sub(left.temp, right.temp, new_temp)
      elif inner_type == Scope.InnerType.FLOAT:
        inst = FSub(left.temp, right.temp, new_temp)
      else:
        raise TypeError(f"Type mismatch for {op.name}")
      
    elif op == BinaryOpNode.OpType.MUL:
      if inner_type == Scope.InnerType.INT:
        inst = Mul(left.temp, right.temp, new_temp)
      elif inner_type == Scope.InnerType.FLOAT:
        inst = FMul(left.temp, right.temp, new_temp)
      else:
        raise TypeError(f"Type mismatch for {op.name}")
      
    elif op == BinaryOpNode.OpType.DIV:
      if inner_type == Scope.InnerType.INT:
        inst = Div(left.temp, right.temp, new_temp)
      elif inner_type == Scope.InnerType.FLOAT:
        inst = FDiv(left.temp, right.temp, new_temp)
      else:
        raise TypeError(f"Type mismatch for {op.name}")
      
    else:
      raise ValueError(f"Invalid binary opcode: {op}")

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
    #  Step 0: create new code object
    co = CodeObject()
    #FILL IN CODE FOR STEP 2

    #  Step 1: add code from child expression
    #  Step 1a: if child is an lval, add a load to get the data
    if expr.lval is True:
      expr = self.rvalify(expr)
    co.code.extend(expr.code)

    #  Step 2: generate instruction to perform unary operation (don't forget to generate right type of op)
    op = node.getOp()
    typ = node.getType()
    inner_type = self._get_inner_type(typ) # FIX: extract inner type
    
    new_temp = self.generateTemp(inner_type)
    inst = None

    if op == UnaryOpNode.OpType.NEG:
      if inner_type == Scope.InnerType.INT:
        inst = Neg(expr.temp, new_temp)
      elif inner_type == Scope.InnerType.FLOAT:
        inst = FNeg(expr.temp, new_temp)
      else:
        raise Exception("Unary minus on unsupported type")

    else:
      raise ValueError(f"Invalid Unary opcode: {op}")

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
    # Step 0: create new code object
    co = CodeObject()
    assert(left.lval is True)

    # Step 1a: if LHS is a variable, generate a load instruction to get the address into a register
	  #          (see generateAddrFromVariable)
    # Step 1b: add code from LHS of assignment (make sure it results in an lval!)
    if left.isVar():
      addr_li = self.generateAddrFromVariable(left)
      co.code.extend(addr_li)
      addr_reg = addr_li.getLast().getDest()
    else:
      co.code.extend(left.code)
      addr_reg = left.temp

    # Step 2: add code from RHS of assignment
    # Step 2a: if right child is an lval, add a load to get the data
    if right.lval is True:
      right = self.rvalify(right)
    co.code.extend(right.code)
    val_reg = right.temp

    # Step 3: generate store (don't forget to generate the right type of store)
    typ = node.getType()
    inner_type = self._get_inner_type(typ) # FIX: extract inner type
    inst = None

    # Handle INT, PTR, and INFER (from malloc) as word stores
    if inner_type in [Scope.InnerType.INT, Scope.InnerType.PTR, Scope.InnerType.INFER]:
      inst = Sw(val_reg, addr_reg, "0")
    elif inner_type == Scope.InnerType.FLOAT:
      inst = Fsw(val_reg, addr_reg, "0")
    else:
      raise TypeError(f"Unsupported type in assignment: {inner_type}")
    
    co.code.append(inst)
    co.lval = False 
    co.temp = None 
    co.type = None 

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

    il = InstructionList()

    typ = node.getType()
    inner_type = self._get_inner_type(typ) # FIX: extract inner type

    if inner_type == Scope.InnerType.INT:
      geti = GetI(self.generateTemp(Scope.InnerType.INT))
      il.append(geti)
      store = InstructionList()
      if var.getSTE().isLocal():
        store.append(Sw(geti.getDest(), "fp", var.getSTE().addressToString()))
      else:
        store.extend(self.generateAddrFromVariable(var));
        store.append(Sw(geti.getDest(), store.getLast().getDest(), "0"))
      il.extend(store)
    elif inner_type == Scope.InnerType.FLOAT:
      getf = GetF(self.generateTemp(Scope.InnerType.FLOAT))
      il.append(getf)
      fstore = InstructionList()
      if var.getSTE().isLocal():
        fstore.append(Fsw(getf.getDest(), "fp", var.getSTE().addressToString()))
      else:
        fstore.extend(self.generateAddrFromVariable(var));
        fstore.append(Fsw(getf.getDest(), fstore.getLast().getDest(), "0"))
      il.extend(fstore)
    else:
      raise Exception("Shouldn't read into other variable")

    co.code.extend(il)
    co.lval = False 
    co.temp = None 
    co.type = None 

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
    typ = node.getWriteExpr().getType()
    inner_type = self._get_inner_type(typ)

    #for strings, we expect a variable
    if node.getWriteExpr().getType().type == Scope.InnerType.STRING:
      #Step 1:
      assert(expr.getSTE() is not None)

      print(f"; generating code to print {expr.getSTE()}")

      #Get the address of the variable
      addrCo = self.generateAddrFromVariable(expr)
      co.code.extend(addrCo)

      #Step 2:
      write = PutS(addrCo.getLast().getDest())
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
      if inner_type == Scope.InnerType.INT or inner_type == Scope.InnerType.PTR:
        write = PutI(expr.temp)
      elif inner_type == Scope.InnerType.FLOAT:
        write = PutF(expr.temp)
      else:
        raise Exception(f"WriteNode has a weird type: {inner_type}")
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

    inner_operand_type = self._get_inner_type(operandType) # FIX: extract inner type

    if inner_operand_type in [Scope.InnerType.INT, Scope.InnerType.PTR]:
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

    elif inner_operand_type == Scope.InnerType.FLOAT:
        result_reg = self.generateTemp(Scope.InnerType.INT)
        co.code.extend(cond.code)
        
        if op == CondNode.OpType.LT:
            co.code.append(Flt(left_temp, right_temp, result_reg))
            co.code.append(Beq(result_reg, "x0", elseLabel))
        elif op == CondNode.OpType.LE:
            co.code.append(Fle(left_temp, right_temp, result_reg))
            co.code.append(Beq(result_reg, "x0", elseLabel))
        elif op == CondNode.OpType.GT:
            co.code.append(Flt(right_temp, left_temp, result_reg))
            co.code.append(Beq(result_reg, "x0", elseLabel))
        elif op == CondNode.OpType.GE:
            co.code.append(Fle(right_temp, left_temp, result_reg))
            co.code.append(Beq(result_reg, "x0", elseLabel))
        elif op == CondNode.OpType.EQ:
            co.code.append(Feq(left_temp, right_temp, result_reg))
            co.code.append(Beq(result_reg, "x0", elseLabel))
        elif op == CondNode.OpType.NE:
            co.code.append(Feq(left_temp, right_temp, result_reg))
            co.code.append(Bne(result_reg, "x0", elseLabel))
    else:
        raise Exception(f"Bad cond type: {inner_operand_type}")
    

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

    inner_operand_type = self._get_inner_type(operandType) # FIX: extract inner type

    co.code.append(loopLabel + ":")

    if inner_operand_type in [Scope.InnerType.INT, Scope.InnerType.PTR]:
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

    elif inner_operand_type == Scope.InnerType.FLOAT:
      result_reg = self.generateTemp(Scope.InnerType.INT)
      
      co.code.extend(cond.code)
      
      if op == CondNode.OpType.LT:
          co.code.append(Flt(left_temp, right_temp, result_reg))
          co.code.append(Beq(result_reg, "x0", outLabel))
      elif op == CondNode.OpType.LE:
          co.code.append(Fle(left_temp, right_temp, result_reg))
          co.code.append(Beq(result_reg, "x0", outLabel))
      elif op == CondNode.OpType.GT:
          co.code.append(Flt(right_temp, left_temp, result_reg))
          co.code.append(Beq(result_reg, "x0", outLabel))
      elif op == CondNode.OpType.GE:
          co.code.append(Fle(right_temp, left_temp, result_reg))
          co.code.append(Beq(result_reg, "x0", outLabel))
      elif op == CondNode.OpType.EQ:
          co.code.append(Feq(left_temp, right_temp, result_reg))
          co.code.append(Beq(result_reg, "x0", outLabel))
      elif op == CondNode.OpType.NE:
          co.code.append(Feq(left_temp, right_temp, result_reg))
          co.code.append(Bne(result_reg, "x0", outLabel))
    else:
        raise Exception("Bad cond type")
    
    co.code.extend(wlist.code)
    co.code.append(J(loopLabel))
    co.code.append(outLabel + ":")

    return co

	# FILL IN FOR STEP 4
	# 
	# Generating code for returns
	# 
	# Step 0: Generate new code object
	# 
	# Step 1: Add retExpr code to code object (rvalify if necessary)
	# 
	# Step 2: Store result of retExpr in appropriate place on stack (fp + 8)
	# 
	# Step 3: Jump to out label (use @link{generateFunctionOutLabel()})
  
  def postprocessReturnNode(self, node: ReturnNode, retExpr: CodeObject) -> CodeObject:
    co = CodeObject()

    if retExpr is not None:
        if retExpr.lval is True:
          retExpr = self.rvalify(retExpr)
        co.code.extend(retExpr.code)

        addr_reg = self.generateTemp(Scope.InnerType.INT)
        co.code.append(Addi("fp", '8', addr_reg))

        ret_type = retExpr.getType()
        inner_type = self._get_inner_type(ret_type) # FIX: extract inner type

        # Allow INT, PTR, and INFER (from malloc)
        if inner_type in [Scope.InnerType.INT, Scope.InnerType.PTR, Scope.InnerType.INFER]:
          co.code.append(Sw(retExpr.temp, addr_reg, "0"))
        elif inner_type == Scope.InnerType.FLOAT:
          co.code.append(Fsw(retExpr.temp, addr_reg, "0"))
        else:
          raise TypeError(f"Unsupported return type: {inner_type}")
    
    co.code.append(J(self.generateFunctionOutLabel()))
    co.lval = False
    co.type = None
    co.temp = None
    return co
  
  def preprocessFunctionNode(self, node: FunctionNode):
		#Generate function label information, used for other labels inside function

    self.currFunc = node.getFuncName()

		# reset register counts; each function uses new registers!
    self.intRegCount = 0
    self.floatRegCount = 0

	# FILL IN FOR STEP 4
	# 
	# Generate code for functions
	# 
	# Step 1: add the label for the beginning of the function
	# 
	# Step 2: manage frame  pointer
	# 			a. Save old frame pointer
	# 			b. Move frame pointer to point to base of activation record (current sp)
	# 			c. Update stack pointer
	# 
	# Step 3: allocate new stack frame (use scope infromation from FunctionNode)
	# 
	# Step 4: save registers on stack (Can inspect intRegCount and floatRegCount to know what to save)
	# 
	# Step 5: add the code from the function body
	# 
	# Step 6: add post-processing code:
	# 			a. Label for `return` statements inside function body to jump to
	# 			b. Restore registers
	# 			c. Deallocate stack frame (set stack pointer to frame pointer)
	# 			d. Reset fp to old location
	# 			e. Return from function

  def postprocessFunctionNode(self, node: FunctionNode, body: CodeObject) -> CodeObject:
    co = CodeObject()

    # FILL IN
	  # Step 1: add the label for the beginning of the function
    co.code.append(Label(self.generateFunctionLabel(node.getFuncName())))
    local_num = node.getScope().getNumLocals()
    reg_int_num = self.intRegCount
    reg_float_num = self.floatRegCount


    # Step 2: manage frame  pointer
    ra_slot_space = 4
    local_space = local_num * 4
    reg_total_space = (reg_int_num + reg_float_num) * 4

    sp_move_total = ra_slot_space + local_space + reg_total_space
    ra_offset = -(ra_slot_space + local_space)
    # 			a. Save old frame pointer
    co.code.append(Addi("sp", "-4", "sp"))
    co.code.append(Sw("fp", "sp", "0"))
    # 			b. Move frame pointer to point to base of activation record (current sp)
    co.code.append(Mv("sp", "fp"))
    # 			c. Update stack pointer

    # Step 3: allocate new stack frame (use scope infromation from FunctionNode)
    if (sp_move_total > 0):
      co.code.append(Addi("sp", str(-sp_move_total), "sp"))
      
    
    co.code.append(Sw("ra", "fp", str(ra_offset)))

	  # Step 4: save registers on stack (Can inspect intRegCount and floatRegCount to know what to save)
    for i in range(reg_int_num):
      reg_offset = ra_offset + -(i + 1) * 4
      co.code.append(Sw(self.intTempPrefix + str(i), "fp", str(reg_offset)))
    for i in range(reg_float_num):
      reg_offset = ra_offset - reg_int_num * 4 - (i + 1) * 4
      co.code.append(Fsw(self.floatTempPrefix + str(i), "fp", str(reg_offset)))

	  # Step 5: add the code from the function body
    co.code.extend(body.code)

    # Step 6: add post-processing code:
    # 			a. Label for `return` statements inside function body to jump to
    co.code.append(Label(self.generateFunctionOutLabel()))

    # 			b. Restore registers
    for i in range(reg_float_num - 1, -1, -1):
      reg_offset = ra_offset - reg_int_num * 4 - (i + 1) * 4
      co.code.append(Flw(self.floatTempPrefix + str(i), "fp", str(reg_offset)))
    for i in range(reg_int_num - 1, -1, -1):
      reg_offset = ra_offset + -(i + 1) * 4
      co.code.append(Lw(self.intTempPrefix + str(i), "fp", str(reg_offset)))

    co.code.append(Lw("ra", "fp", str(ra_offset)))
    # 			c. Deallocate stack frame (set stack pointer to frame pointer)
    co.code.append(Mv("fp", "sp"))
    # 			d. Reset fp to old location
    co.code.append(Lw("fp", "sp", "0"))
    co.code.append(Addi("sp", "4", "sp"))
    # 			e. Return from function
    co.code.append(Ret())


    return co

	# Generate code for the list of functions. This is the "top level" code generation function
	# 
	# Step 1: Set fp to point to sp
	# 
	# Step 2: Insert a JR to main
	# 
	# Step 3: Insert a HALT
	# 
	# Step 4: Include all the code of the functions

  def postprocessFunctionListNode(self, node: FunctionListNode, functions: List[CodeObject]) -> CodeObject:
    co = CodeObject()

    co.code.append(Mv("sp", "fp"))
    co.code.append(Jr(self.generateFunctionLabel("main")))
    co.code.append(Halt())
    co.code.append(Blank())

    # Add code for each of the functions
    for c in functions:
      co.code.extend(c.code)
      co.code.append(Blank())
    
    return co

	# FILL IN FOR STEP 4
	# 
	# Generate code for a call expression
	# 
	# Step 1: For each argument:
	# 
	# 	Step 1a: insert code of argument (don't forget to rvalify!)
	# 
	# 	Step 1b: push result of argument onto stack 
	# 
	# Step 2: alloate space for return value
	# 
	# Step 3: push current return address onto stack
	# 
	# Step 4: jump to function
	# 
	# Step 5: pop return address back from stack
	# 
	# Step 6: pop return value into fresh temporary (destination of call expression)
	# 
	# Step 7: remove arguments from stack (move sp)
  #
  # FOR STEP 6: Add special handling for malloc and free
  #
  # FOR STEP 6: Make sure to handle VOID functions properly
  def postprocessCallNode(self, node: CallNode, args: List[CodeObject]) -> CodeObject:
    co = CodeObject()

    args_num = len(args)
    args_space = args_num * 4
    return_type = node.getType()
    inner_ret_type = self._get_inner_type(return_type)

    rv_slots = 4
    ra_slots = 4
    
    caller_total_space = args_space + rv_slots + ra_slots

    # Step 2: alloate space for return value
    if (caller_total_space > 0):
      co.code.append(Addi("sp", str(-caller_total_space), "sp"))
    # Step 1: For each argument:
    # 	Step 1a: insert code of argument (don't forget to rvalify!)
    for i, arg in enumerate(args):
      arg_offset = rv_slots + ra_slots + (args_num - i - 1) * 4

      if arg.lval:
        arg = self.rvalify(arg)
      co.code.extend(arg.code)

      arg_inner_type = self._get_inner_type(arg.getType())
      
    # 	Step 1b: push result of argument onto stack 
      if arg_inner_type in [Scope.InnerType.INT, Scope.InnerType.PTR, Scope.InnerType.INFER]:
        co.code.append(Sw(arg.temp, "sp", str(arg_offset)))
      elif arg_inner_type == Scope.InnerType.FLOAT:
        co.code.append(Fsw(arg.temp, "sp", str(arg_offset)))
  	
	  # Step 3: push current return address onto stack
    co.code.append(Sw("ra", "sp", "0"))

	  # Step 4: jump to function
    co.code.append(Jr(self.generateFunctionLabel(node.getFuncName())))

  	# Step 5: pop return address back from stack
    co.code.append(Lw("ra", "sp", "0"))

	  # Step 6: pop return value into fresh temporary (destination of call expression)
    rv_offset = ra_slots
    if inner_ret_type != Scope.InnerType.VOID:
      new_temp = self.generateTemp(inner_ret_type)
      if inner_ret_type in [Scope.InnerType.INT, Scope.InnerType.PTR, Scope.InnerType.INFER]:
        co.code.append(Lw(new_temp, "sp", str(rv_offset)))
      elif inner_ret_type == Scope.InnerType.FLOAT:
        co.code.append(Flw(new_temp, "sp", str(rv_offset)))

      co.lval = False
      co.type = return_type
      co.temp = new_temp

    else:
      co.lval = False
      co.type = Scope.Type(Scope.InnerType.VOID)
      co.temp = None

  	# Step 7: remove arguments from stack (move sp)
    if (caller_total_space > 0):
      co.code.append(Addi("sp", str(caller_total_space), "sp"))

    return co
	 
   # Generate code for * (expr)
	 # 
	 # Goal: convert the r-val coming from expr (a computed address) into an l-val (an address that can be loaded/stored)
	 # 
	 # Step 0: Create new code object
	 # 
	 # Step 1: Rvalify expr if needed
	 # 
	 # Step 2: Copy code from expr (including any rvalification) into new code object
	 # 
	 # Step 3: New code object has same temporary as old code, but now is marked as an l-val
	 # 
	 # Step 4: New code object has an "unwrapped" type: if type of expr is * T, type of temporary is T. Can get this from node
  def postprocessPtrDerefNode(self, node: PtrDerefNode, expr: CodeObject) -> CodeObject:
    # Step 0: Create new code object
    co = CodeObject()

    # Step 1: Rvalify expr if needed
    if expr.lval is True:
      expr = self.rvalify(expr)

    # Step 2: Copy code from expr (including any rvalification) into new code object
    co.code.extend(expr.code)

    # Step 3: New code object has same temporary as old code, but now is marked as an l-val
    co.lval = True
    co.temp = expr.temp

    # Step 4: New code object has an "unwrapped" type: if type of expr is * T, type of temporary is T. Can get this from node
    co.type = node.getType()
    return co

 # Generate code for a & (expr)
 # 
 # Goal: convert the lval coming from expr (an address) to an r-val (a piece of data that can be used)
 # 
 # Step 0: Create new code object
 # 
 # Step 1: If lval is a variable, generate code to put address into a register (e.g., generateAddressFromVar)
 #			Otherwise just copy code from other code object
 # 
 # Step 2: New code object has same temporary as existing code, but is an r-val
 # 
 # Step 3: New code object has a "wrapped" type. If type of expr is T, type of temporary is *T. Can get this from node
  def postprocessAddrOfNode(self, node: AddrOfNode, expr: CodeObject) -> CodeObject:
    # Step 0: Create new code object
    co = CodeObject()

    # Step 1: If lval is a variable, generate code to put address into a register (e.g., generateAddressFromVar)
    #			Otherwise just copy code from other code object
    if expr.isVar():
      addr_instrs = self.generateAddrFromVariable(expr)
      co.code.extend(addr_instrs)
      co.temp = addr_instrs.getLast().getDest()
    else:
      co.code.extend(expr.code)
      co.temp = expr.temp
    
    # Step 2: New code object has same temporary as existing code, but is an r-val
    co.lval = False

    # Step 3: New code object has a "wrapped" type. If type of expr is T, type of temporary is *T. Can get this from node
    co.type = node.getType()
    return co

	# Generate code for malloc
	# 
	# Step 0: Create new code object
	# 
	# Step 1: Add code from expression (rvalify if needed)
	# 
	# Step 2: Create new MALLOC instruction
	# 
	# Step 3: Set code object type to INFER
  def postprocessMallocNode(self, node: MallocNode, expr: CodeObject) -> CodeObject:
    # Step 0: Create new code object
    co = CodeObject()

    # Step 1: Add code from expression (rvalify if needed)
    if expr.lval is True:
        expr = self.rvalify(expr)
    co.code.extend(expr.code)
    
    # Step 2: Create new MALLOC instruction
    dest_reg = self.generateTemp(Scope.InnerType.PTR)
    co.code.append(Malloc(expr.temp, dest_reg))
    
    co.lval = False
    co.temp = dest_reg

    # Step 3: Set code object type to INFER
    co.type = Scope.Type(Scope.InnerType.INFER)
    return co

	#  Generate code for free
	#  
	#  Step 0: Create new code object
	#  
	#  Step 1: Add code from expression (rvalify if needed)
	#  
	#  Step 2: Create new FREE instruction
  def postprocessFreeNode(self, node: FreeNode, expr: CodeObject) -> CodeObject:
    #  Step 0: Create new code object
    co = CodeObject()

    #  Step 1: Add code from expression (rvalify if needed)
    if expr.lval is True:
        expr = self.rvalify(expr)
    co.code.extend(expr.code)

    #  Step 2: Create new FREE instruction
    co.code.append(Free(expr.temp))
    
    co.lval = False
    co.type = Scope.Type(Scope.InnerType.VOID)
    return co

  # CastNode for Step7
  def postprocessCastNode(self, node: CastNode, expr: CodeObject) -> CodeObject:
    co = CodeObject()
    
    if expr.lval is True:
        expr = self.rvalify(expr)
        
    co.code.extend(expr.code)
    
    co.lval = False
    co.temp = expr.temp
    co.type = node.getCastType()
    
    return co

	# Generate a fresh temporary
	# 
	# @return new temporary register name
  
  def generateTemp(self, t: Scope.InnerType) -> str:

    if t == Scope.InnerType.INT or t == Scope.InnerType.PTR or t == Scope.InnerType.INFER:
      s = self.intTempPrefix + str(self.intRegCount)
      self.intRegCount += 1
      return s
    elif t == Scope.InnerType.FLOAT:
      s = self.floatTempPrefix + str(self.floatRegCount)
      self.floatRegCount += 1
      return s
    else:
      raise Exception(f"Generating temp for bad type: {t}")

  def generateLoopLabel(self) -> str:
    self.loopLabel += 1
    return "loop_" + str(self.loopLabel)

  def generateElseLabel(self) -> str:
    self.elseLabel += 1
    return "else_" + str(self.elseLabel)

  def generateOutLabel(self) -> str:
    self.outLabel += 1
    return "out_" + str(self.outLabel)
  
  def generateFunctionLabel(self, func = None) -> str:
    if func is None:
      return "func_" + self.currFunc
    else:
      return "func_" + func
    
  def generateFunctionOutLabel(self) -> str:
    return "func_ret_" + self.currFunc
  

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
    co = CodeObject()
    assert(lco.lval is True)

    if lco.isVar():
      addr_li = self.generateAddrFromVariable(lco)
      co.code.extend(addr_li)
      addr_reg = addr_li.getLast().getDest()
    else:
      co.code.extend(lco.code)
      addr_reg = lco.temp

    typ = lco.getType()
    inner_type = self._get_inner_type(typ) # FIX: extract inner type

    new_temp = self.generateTemp(inner_type)
    
    if inner_type in [Scope.InnerType.INT, Scope.InnerType.PTR, Scope.InnerType.INFER]:
      inst = Lw(new_temp, addr_reg, "0")
    elif inner_type == Scope.InnerType.FLOAT:
      inst = Flw(new_temp, addr_reg, "0")
    else:
      raise Exception(f"Shouldn't rvalify into other variable: {inner_type}")

    co.code.append(inst)
    co.lval = False
    co.temp = new_temp
    co.type = typ
    return co

	# Generate an instruction sequence that holds the address of the variable in a code object
	# 
	# If it's a global variable, just get the address from the symbol table
	# 
	# If it's a local variable, compute the address relative to the frame pointer (fp)
	# 
	# @param lco The code object holding a variable
	# @return a list of instructions that puts the address of the variable in a register

  def generateAddrFromVariable(self, lco: CodeObject) -> InstructionList:
    il = InstructionList()

    #Step 1:
    symbol = lco.getSTE()
    address = symbol.addressToString()

    #Step 2:
    if symbol.isLocal():
      # If local, address is offset
			# need to load fp + offset
			# addi tmp' fp offset
      compAddr = Addi("fp", address, self.generateTemp(Scope.InnerType.INT))
    else:
			#If global, address in symbol table is the right location
      #la tmp' addr // Register type needs to be an int
      compAddr = La(self.generateTemp(Scope.InnerType.INT), address)
    il.append(compAddr) # add instruction

    return il
