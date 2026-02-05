from .InstructionList import InstructionList
from .instructions import *
from ..compiler import Scope, LocalScope
from .instructions.Instruction import OpCode
import sys

class RegisterAllocator:
    def __init__(self, num_int, num_float, func_scope: LocalScope):
        self.num_int = num_int
        self.num_float = num_float
        self.func_scope = func_scope
        self.global_scope = func_scope.parentTable
        
        self.used_int_regs = set()
        self.used_float_regs = set()

        all_int_regs = []
        for i in range(32):
            if i in [0, 1, 2, 8, 10]: # Skip zero, ra, sp, fp/s0, a0
                continue
            all_int_regs.append(f'x{i}')
            
        limit_int = min(num_int, 32)
        available_int_regs = [r for r in all_int_regs if int(r[1:]) < limit_int]

        if len(available_int_regs) < 3:
             raise Exception(f"Register count {num_int} is too low.")

        self.INT_SCRATCH_REGS = available_int_regs[:2]
        self.int_reg_pool = available_int_regs[2:]

        self.FLOAT_SCRATCH_REGS = ['f0', 'f1']

        limit_float = min(num_float, 32)
        self.float_reg_pool = []
        for i in range(2, limit_float):
            if i == 10: # Skip fa0
                continue
            self.float_reg_pool.append(f'f{i}')

        self.spill_map = {}
        self.current_spill_offset = (func_scope.getNumLocals() * -4)
        self.reg_map = {}

        self.phys_to_var = {} 
        self.var_to_phys = {} 
        self.is_dirty = {} 

        self.lru_queue = []

    def update_lru(self, reg: str):
        if reg in self.lru_queue:
            self.lru_queue.remove(reg)
        self.lru_queue.append(reg)

    def emit_addi_expanded(self, dest, src, imm_str, out):
        try:
            imm = int(imm_str)
        except ValueError:
            out.append(Addi(src, imm_str, dest))
            return

        if -2048 <= imm <= 2047:
            out.append(Addi(src, str(imm), dest))
        else:
            scratch = self.INT_SCRATCH_REGS[0]
            out.append(Li(scratch, str(imm)))
            out.append(Add(src, scratch, dest))

    def emit_ls_expanded(self, opcode_class, reg, base, offset_str, out):
        try:
            offset = int(offset_str)
        except ValueError:
            out.append(opcode_class(reg, base, offset_str))
            return

        if -2048 <= offset <= 2047:
            out.append(opcode_class(reg, base, str(offset)))
        else:
            scratch = self.INT_SCRATCH_REGS[0]
            out.append(Li(scratch, str(offset)))
            out.append(Add(base, scratch, scratch))
            out.append(opcode_class(reg, scratch, "0"))

    def allocate_function(self, func_label, body_3ac, ret_label, enable_dfa=False):
        self.used_int_regs = set()
        self.used_float_regs = set()
        self.reg_map = {}
        self.phys_to_var = {}
        self.var_to_phys = {}
        self.is_dirty = {}
        self.lru_queue = []

        body_instructions = InstructionList()

        num_locals = self.func_scope.getNumLocals()
        temp_int_max = -1
        temp_float_max = -1

        blocks = self.get_basic_blocks(body_3ac.code)

        full_liveness = None
        if enable_dfa:
            blocks = self.dead_code_elimination(blocks)
            full_liveness = self.perform_global_liveness(blocks)

        # reserve stack space
        for block in blocks:
            for instr in block:
                operands = [instr.src1, instr.src2, instr.dest]
                for op in operands:
                    if op and (op.startswith('$t') or op.startswith('$f')):
                        val = int(op[2:])
                        if op.startswith('$t'):
                            temp_int_max = max(temp_int_max, val)
                        else:
                            temp_float_max = max(temp_float_max, val)
        
        if temp_int_max >= len(self.int_reg_pool):
            for i in range(len(self.int_reg_pool), temp_int_max + 1):
                self.get_spill_offset(f'$t{i}')
        if temp_float_max >= len(self.float_reg_pool):
            for i in range(len(self.float_reg_pool), temp_float_max + 1):
                self.get_spill_offset(f'$f{i}')

        # main allocation loop
        for i, block in enumerate(blocks):
            self.phys_to_var = {}
            self.var_to_phys = {}
            self.is_dirty = {}
            self.lru_queue = []
            
            if enable_dfa:
                liveness = full_liveness[i]
            else:
                liveness = self.compute_liveness(block)
                
            self.allocate_block(block, liveness, body_instructions)

        sorted_used_int = sorted(list(self.used_int_regs))
        sorted_used_float = sorted(list(self.used_float_regs))

        local_vars_size = num_locals * 4
        spill_vars_size = len(self.spill_map) * 4
        base_local_size = local_vars_size + spill_vars_size

        saved_regs_size = (len(sorted_used_int) + len(sorted_used_float)) * 4

        header_size = 12
        total_needed = header_size + base_local_size + saved_regs_size
        frame_size = (total_needed + 15) // 16 * 16

        # Prologue
        out = InstructionList()
        out.append(Label(func_label))
        
        if frame_size > 0:
            self.emit_addi_expanded("sp", "sp", str(-frame_size), out)
        
        fp_offset_from_sp = frame_size - 12
        
        self.emit_ls_expanded(Sw, "ra", "sp", str(fp_offset_from_sp + 4), out)
        self.emit_ls_expanded(Sw, "fp", "sp", str(fp_offset_from_sp), out)
        self.emit_addi_expanded("fp", "sp", str(fp_offset_from_sp), out)
        
        current_save_offset = -base_local_size - 4
        
        out.append(Blank("Saving registers"))
        for reg in sorted_used_int:
            self.emit_ls_expanded(Sw, reg, "fp", str(current_save_offset), out)
            current_save_offset -= 4
        for reg in sorted_used_float:
            self.emit_ls_expanded(Fsw, reg, "fp", str(current_save_offset), out)
            current_save_offset -= 4
        out.append(Blank())

        # Body
        out.extend(body_instructions)

        # Epilogue
        out.append(Label(ret_label))

        out.append(Blank("Restore registers"))

        current_save_offset = -base_local_size - 4
        for reg in sorted_used_int:
            self.emit_ls_expanded(Lw, reg, "fp", str(current_save_offset), out)
            current_save_offset -= 4
        for reg in sorted_used_float:
            self.emit_ls_expanded(Flw, reg, "fp", str(current_save_offset), out)
            current_save_offset -= 4

        self.emit_ls_expanded(Lw, "ra", "fp", "4", out)
        self.emit_ls_expanded(Lw, "fp", "fp", "0", out)
        if frame_size > 0:
            self.emit_addi_expanded("sp", "sp", str(frame_size), out)
            
        out.append(Ret())

        return out

    def get_basic_blocks(self, code_list: InstructionList):
        blocks = []
        current_block = []
        
        for i, instr in enumerate(code_list):
            if isinstance(instr, Label):
                if current_block:
                    blocks.append(current_block)
                    current_block = []
                current_block.append(instr)
                continue
            
            current_block.append(instr)
            
            oc = instr.getOC()

            if oc in [OpCode.BEQ, OpCode.BNE, OpCode.BLT, OpCode.BLE, OpCode.BGT, OpCode.BGE, 
                      OpCode.J, OpCode.JR, OpCode.RET]:
                blocks.append(current_block)
                current_block = []
        
        if current_block:
            blocks.append(current_block)
            
        return blocks
    
    def is_var(self, op):
        return op and (op.startswith('$t') or op.startswith('$f') or op.startswith('$l') or op.startswith('$g'))

    def compute_liveness(self, block: list):
        live_set = set() 
        liveness_info = [set() for _ in range(len(block))]
        
        for i in range(len(block) - 1, -1, -1):
            liveness_info[i] = set(live_set)

            instr = block[i]
            src1, src2, dest = instr.src1, instr.src2, instr.dest
            
            if dest and (dest.startswith('$t') or dest.startswith('$f')):
                if dest in live_set:
                    live_set.remove(dest)

            for op in [src1, src2]:
                if op and (op.startswith('$t') or op.startswith('$f') or op.startswith('$l') or op.startswith('$g')):
                    live_set.add(op)
            
        return liveness_info

    def perform_global_liveness(self, blocks):
        label_to_block = {}
        for i, block in enumerate(blocks):
            if block and isinstance(block[0], Label):
                label_to_block[block[0].label] = i
        
        succ = [[] for _ in blocks]
        for i, block in enumerate(blocks):
            if not block:
                if i + 1 < len(blocks): succ[i].append(i+1)
                continue
            
            last = block[-1]
            oc = last.getOC()
            
            if oc in [OpCode.BEQ, OpCode.BNE, OpCode.BLT, OpCode.BLE, OpCode.BGT, OpCode.BGE]:
                target = last.label
                if target in label_to_block: succ[i].append(label_to_block[target])
                if i + 1 < len(blocks): succ[i].append(i+1)
            elif oc == OpCode.J:
                target = last.label
                if target in label_to_block: succ[i].append(label_to_block[target])
            elif oc == OpCode.RET:
                pass
            elif oc == OpCode.JR:
                if i + 1 < len(blocks): succ[i].append(i+1)
            else:
                if i + 1 < len(blocks): succ[i].append(i+1)

        use = [set() for _ in blocks]
        def_ = [set() for _ in blocks]
        all_globals = set()

        for i, block in enumerate(blocks):
            for instr in block:
                oc = instr.getOC()
                src1, src2, dest = instr.src1, instr.src2, instr.dest
                
                reads = []
                writes = []
                
                if oc in [OpCode.SW, OpCode.FSW]:
                    if dest: reads.append(dest)
                    if src1: reads.append(src1)
                else:
                    if src1: reads.append(src1)
                    if src2: reads.append(src2)
                    if dest: writes.append(dest)
                
                if isinstance(instr, PushInt) or isinstance(instr, PushFloat):
                    if instr.src1: reads.append(instr.src1)

                for op in [src1, src2, dest]:
                    if op and op.startswith('$g'): all_globals.add(op)

                for r in reads:
                    if self.is_var(r) and r not in def_[i]:
                        use[i].add(r)
                
                for w in writes:
                    if self.is_var(w):
                        def_[i].add(w)

        in_ = [set() for _ in blocks]
        out_ = [set() for _ in blocks]
        
        for i in range(len(blocks)):
            if not succ[i]:
                out_[i] = set(all_globals)

        changed = True
        while changed:
            changed = False
            for i in range(len(blocks) - 1, -1, -1):
                new_out = set()
                if not succ[i]:
                    new_out = set(all_globals)
                else:
                    for s in succ[i]:
                        new_out |= in_[s]
                
                if new_out != out_[i]:
                    out_[i] = new_out
                    changed = True
                
                new_in = use[i] | (out_[i] - def_[i])
                if new_in != in_[i]:
                    in_[i] = new_in
                    changed = True

        full_liveness = []
        for i, block in enumerate(blocks):
            block_liveness = [set() for _ in range(len(block))]
            current_live = out_[i].copy()
            
            for j in range(len(block) - 1, -1, -1):
                block_liveness[j] = set(current_live)
                
                instr = block[j]
                oc = instr.getOC()
                src1, src2, dest = instr.src1, instr.src2, instr.dest
                
                reads = []
                writes = []
                if oc in [OpCode.SW, OpCode.FSW]:
                    if dest: reads.append(dest)
                    if src1: reads.append(src1)
                else:
                    if dest: writes.append(dest)
                    if src1: reads.append(src1)
                    if src2: reads.append(src2)
                
                if isinstance(instr, PushInt) or isinstance(instr, PushFloat):
                    if instr.src1: reads.append(instr.src1)

                for w in writes:
                    if self.is_var(w) and w in current_live:
                        current_live.remove(w)
                
                for r in reads:
                    if self.is_var(r):
                        current_live.add(r)
            
            full_liveness.append(block_liveness)
            
        return full_liveness

    def has_side_effect(self, instr):
        oc = instr.getOC()
        if oc in [OpCode.BEQ, OpCode.BNE, OpCode.BLT, OpCode.BLE, OpCode.BGT, OpCode.BGE, 
                  OpCode.J, OpCode.JR, OpCode.RET]:
            return True
        if oc in [OpCode.SW, OpCode.FSW]:
            return True
        if oc in [OpCode.PUTS, OpCode.PUTI, OpCode.PUTF, OpCode.GETI, OpCode.GETF]:
            return True
        if isinstance(instr, Label):
            return True
        if isinstance(instr, PushInt) or isinstance(instr, PushFloat):
            return True
        return False

    def dead_code_elimination(self, blocks):
        while True:
            full_liveness = self.perform_global_liveness(blocks)
            changed = False
            new_blocks = []
            
            for i, block in enumerate(blocks):
                new_block = []
                block_live = full_liveness[i]
                
                for j, instr in enumerate(block):
                    oc = instr.getOC()
                    live_after = block_live[j]
                    
                    is_dead = False
                    if not self.has_side_effect(instr):
                        dest = instr.dest
                        if dest and self.is_var(dest):
                           if dest not in live_after:
                                is_dead = True
                                changed = True
                    
                    if not is_dead:
                        new_block.append(instr)
                new_blocks.append(new_block)
            
            blocks = new_blocks
            if not changed:
                break
        return blocks
    
    def allocate_block(self, block: list, liveness_info: list, out: InstructionList):
        for i, instr in enumerate(block):
            oc = instr.getOC()
            src1, src2, dest = instr.src1, instr.src2, instr.dest
            
            live_after = liveness_info[i]

            if isinstance(instr, Label):
                out.append(instr)
                continue

            if oc == OpCode.RET:
                regs_to_check = list(self.phys_to_var.keys())
                for r in regs_to_check:
                    var = self.phys_to_var[r]
                    if var.startswith('$g'):
                        self.spill_reg(r, out)
                    else:
                        self.forget_reg(r)
                out.append(instr)
                self.clear_regs()
                continue

            if oc == OpCode.J:
                regs_to_check = list(self.phys_to_var.keys())
                for r in regs_to_check:
                    var = self.phys_to_var[r]
                    if var.startswith('$t') or var.startswith('$f'):
                        self.forget_reg(r)
                    else:
                        self.spill_reg(r, out)
                out.append(instr)
                self.clear_regs()
                continue

            if oc == OpCode.JR:
                regs_to_spill = [r for r in self.phys_to_var.keys()]
                for r in regs_to_spill:
                    self.spill_reg(r, out)
                out.append(instr)
                continue
            
            if oc in [OpCode.BEQ, OpCode.BNE, OpCode.BLT, OpCode.BLE, OpCode.BGT, OpCode.BGE]:
                op_type = self.get_operand_type(src1)
                is_float = (op_type == Scope.Type.FLOAT)

                r1 = self.ensure(src1, out, is_float_hint=is_float, live_after=live_after, locked_regs=[])
                
                is_src2_lit = not (src2.startswith('$') or src2.startswith('%')) and (src2[0].isdigit() or src2[0] in '-.')
                if is_src2_lit:
                    scratches = self.FLOAT_SCRATCH_REGS if is_float else self.INT_SCRATCH_REGS
                    if r1 == scratches[0]:
                        if is_float: out.append(FImm(scratches[1], src2))
                        else:        out.append(Li(scratches[1], src2))
                        r2 = scratches[1]
                    else:
                        r2 = self.ensure(src2, out, is_float_hint=is_float, live_after=live_after, locked_regs=[r1])
                else:
                    r2 = self.ensure(src2, out, is_float_hint=is_float, live_after=live_after, locked_regs=[r1])

                current_regs = list(self.phys_to_var.keys())
                for r in current_regs:
                    self.spill_reg(r, out)

                if not is_float:
                    br = InstructionBranch(r1, r2, instr.label)
                    br.oc = oc
                    out.append(br)
                else:
                    cmp_reg = self.INT_SCRATCH_REGS[0]
                    if oc == OpCode.BLT:
                        out.append(Flt(r1, r2, cmp_reg))
                        out.append(Bne(cmp_reg, "x0", instr.label))
                    elif oc == OpCode.BLE:
                        out.append(Fle(r1, r2, cmp_reg))
                        out.append(Bne(cmp_reg, "x0", instr.label))
                    elif oc == OpCode.BGT:
                        out.append(Flt(r2, r1, cmp_reg))
                        out.append(Bne(cmp_reg, "x0", instr.label))
                    elif oc == OpCode.BGE:
                        out.append(Fle(r2, r1, cmp_reg))
                        out.append(Bne(cmp_reg, "x0", instr.label))
                    elif oc == OpCode.BEQ:
                        out.append(Feq(r1, r2, cmp_reg))
                        out.append(Bne(cmp_reg, "x0", instr.label))
                    elif oc == OpCode.BNE:
                        out.append(Feq(r1, r2, cmp_reg))
                        out.append(Beq(cmp_reg, "x0", instr.label))

                self.clear_regs()
                continue

            if oc == OpCode.MV or oc == OpCode.FMVS:
                if src1 in self.var_to_phys:
                    phys_src = self.var_to_phys[src1]
                    is_temp = src1.startswith('$t') or src1.startswith('$f')
                    
                    if is_temp and src1 not in live_after:
                        del self.phys_to_var[phys_src]
                        del self.var_to_phys[src1]
                        if phys_src in self.is_dirty: del self.is_dirty[phys_src]
                        self.phys_to_var[phys_src] = dest
                        self.var_to_phys[dest] = phys_src
                        self.is_dirty[phys_src] = True 
                        self.update_lru(phys_src)
                        
                        if oc == OpCode.FMVS: self.used_float_regs.add(phys_src)
                        else: self.used_int_regs.add(phys_src)
                        continue

            if isinstance(instr, PushInt):
                phys_reg = self.ensure(src1, out, is_float_hint=False, live_after=live_after, locked_regs=[])
                out.append(Addi("sp", "-4", "sp"))
                out.append(Sw(phys_reg, "sp", "0"))
                continue
            elif isinstance(instr, PushFloat):
                phys_reg = self.ensure(src1, out, is_float_hint=True, live_after=live_after, locked_regs=[])
                out.append(Addi("sp", "-4", "sp"))
                out.append(Fsw(phys_reg, "sp", "0"))
                continue
            
            if oc == OpCode.ADDI:
                phys_src1 = self.ensure(src1, out, is_float_hint=False, live_after=live_after, locked_regs=[])
                phys_dest = self.ensure(dest, out, for_writing=True, is_float_hint=False, live_after=live_after, locked_regs=[phys_src1])
                self.is_dirty[phys_dest] = True
                self.emit_addi_expanded(phys_dest, phys_src1, src2, out)
                self.free_dead_temps(live_after)
                continue
            
            is_float_instr = oc in [OpCode.FADDS, OpCode.FSUBS, OpCode.FMULS, OpCode.FDIVS, 
                                    OpCode.FNEGS, OpCode.FMVS, OpCode.FIMMS, OpCode.GETF, 
                                    OpCode.PUTF, OpCode.FLW, OpCode.FSW]

            phys_src1 = None
            phys_src2 = None
            
            if src1: phys_src1 = self.ensure(src1, out, for_writing=False, is_float_hint=is_float_instr, live_after=live_after, locked_regs=[])
            if src2: phys_src2 = self.ensure(src2, out, for_writing=False, is_float_hint=is_float_instr, live_after=live_after, locked_regs=[phys_src1] if phys_src1 else [])

            phys_dest = None
            if dest:
                phys_dest = self.ensure(dest, out, for_writing=True, is_float_hint=is_float_instr, live_after=live_after, locked_regs=[r for r in [phys_src1, phys_src2] if r])
                self.is_dirty[phys_dest] = True

            new_instr = self.create_machine_instruction(oc, phys_src1, phys_src2, phys_dest, instr)
            if new_instr:
                out.append(new_instr)

            self.free_dead_temps(live_after)

        regs_to_spill = [r for r in self.phys_to_var.keys()]
        for r in regs_to_spill:
            self.spill_reg(r, out)

    def free_dead_temps(self, live_after):
        regs_to_free = []
        for p_reg, var in self.phys_to_var.items():
            is_temp = var.startswith('$t') or var.startswith('$f')
            if is_temp and var not in live_after:
                regs_to_free.append(p_reg)
        for r in regs_to_free:
            self.free(r)

    def clear_regs(self):
        self.phys_to_var = {}
        self.var_to_phys = {}
        self.is_dirty = {}
        self.lru_queue = []

    def forget_reg(self, phys_reg):
        if phys_reg in self.phys_to_var:
            var = self.phys_to_var[phys_reg]
            del self.phys_to_var[phys_reg]
            if var in self.var_to_phys: del self.var_to_phys[var]
            if phys_reg in self.is_dirty: del self.is_dirty[phys_reg]
        if phys_reg in self.lru_queue:
            self.lru_queue.remove(phys_reg)

    def ensure(self, operand: str, out: InstructionList, for_writing=False, is_float_hint=False, live_after=None, locked_regs=None):
        if operand in ['sp', 'fp', 'ra', 'gp', 'tp', 'zero'] or \
           operand.startswith('x') and operand[1:].isdigit() or \
           operand.startswith('f') and operand[1:].isdigit():
            return operand
        
        if not (operand.startswith('$') or operand.startswith('%')): 
             if operand[0].isdigit() or operand[0] == '-' or operand[0] == '.':
                 is_float_lit = '.' in operand
                 scratch = self.FLOAT_SCRATCH_REGS[0] if is_float_lit else self.INT_SCRATCH_REGS[0]
                 if is_float_lit:
                     out.append(FImm(scratch, operand))
                 else:
                     out.append(Li(scratch, operand))
                 return scratch

        if operand == '$ret':
            is_float = is_float_hint
        else:
            op_type = self.get_operand_type(operand)
            is_float = (op_type == Scope.Type.FLOAT)
        
        if operand in self.var_to_phys:
            reg = self.var_to_phys[operand]
            self.update_lru(reg)
            return reg

        chosen_reg = self.allocate_reg(operand, is_float, out, live_after, locked_regs)

        if not for_writing:
            if operand.startswith('$t') or operand.startswith('$f'):
                 offset = self.get_spill_offset(operand)
                 if is_float:
                     self.emit_ls_expanded(Flw, chosen_reg, "fp", str(offset), out)
                 else:
                     self.emit_ls_expanded(Lw, chosen_reg, "fp", str(offset), out)
            elif operand.startswith('$l'):
                 offset = operand[2:]
                 if is_float:
                     self.emit_ls_expanded(Flw, chosen_reg, "fp", offset, out)
                 else:
                     self.emit_ls_expanded(Lw, chosen_reg, "fp", offset, out)
            elif operand.startswith('$g'):
                 addr_reg = self.INT_SCRATCH_REGS[1]
                 var_name = operand[2:]
                 ste = self.global_scope.getSymbolTableEntry(var_name)
                 if ste.getType() == Scope.Type.STRING:
                     out.append(La(chosen_reg, ste.addressToString()))
                 else:
                     out.append(La(addr_reg, ste.addressToString()))
                     if is_float:
                         out.append(Flw(chosen_reg, addr_reg, "0"))
                     else:
                         out.append(Lw(chosen_reg, addr_reg, "0"))
            elif operand == '$ret_i':
                 out.append(Mv("a0", chosen_reg))
            elif operand == '$ret_f':
                 out.append(FMv("fa0", chosen_reg))
            elif operand == '$ret':
                 if is_float: out.append(FMv("fa0", chosen_reg))
                 else:        out.append(Mv("a0", chosen_reg))

        return chosen_reg

    def allocate_reg(self, operand: str, is_float: bool, out: InstructionList, live_after=None, locked_regs=None):
        pool = self.float_reg_pool if is_float else self.int_reg_pool
        locked_regs = locked_regs or []
        
        chosen_reg = None

        if chosen_reg is None:
            for reg in pool:
                if reg not in self.phys_to_var:
                    chosen_reg = reg
                    break
        
        if chosen_reg is None and live_after is not None:
            for reg in pool:
                if reg in locked_regs: continue
                if reg in self.phys_to_var:
                    var = self.phys_to_var[reg]
                    if var.startswith('$t') or var.startswith('$f'):
                        if var not in live_after and var != operand:
                            self.forget_reg(reg)
                            chosen_reg = reg
                            break

        if chosen_reg is None:
            chosen_reg = self.pick_spill_victim(is_float, locked_regs)
            self.spill_reg(chosen_reg, out)

        self.phys_to_var[chosen_reg] = operand
        self.var_to_phys[operand] = chosen_reg
        self.is_dirty[chosen_reg] = False 
        self.update_lru(chosen_reg)

        if is_float:
            self.used_float_regs.add(chosen_reg)
        else:
            self.used_int_regs.add(chosen_reg)
            
        return chosen_reg

    def spill_reg(self, phys_reg: str, out: InstructionList):
        if phys_reg not in self.phys_to_var:
            return

        var_name = self.phys_to_var[phys_reg]
        
        if self.is_dirty.get(phys_reg, False):
            if var_name.startswith('$t') or var_name.startswith('$f'):
                 offset = self.get_spill_offset(var_name)
                 if phys_reg.startswith('f'):
                     self.emit_ls_expanded(Fsw, phys_reg, "fp", str(offset), out)
                 else:
                     self.emit_ls_expanded(Sw, phys_reg, "fp", str(offset), out)
            else:
                 self.store_reg_to_operand(phys_reg, var_name, out)
                 
            self.is_dirty[phys_reg] = False

        del self.phys_to_var[phys_reg]
        if var_name in self.var_to_phys:
            del self.var_to_phys[var_name]

    def free(self, phys_reg: str):
        if phys_reg in self.phys_to_var:
            var_name = self.phys_to_var[phys_reg]
            del self.phys_to_var[phys_reg]
            if var_name in self.var_to_phys:
                del self.var_to_phys[var_name]
            if phys_reg in self.is_dirty:
                del self.is_dirty[phys_reg]
            
        if phys_reg in self.lru_queue:
            self.lru_queue.remove(phys_reg)

    def pick_spill_victim(self, is_float, locked_regs=None):
        pool = self.float_reg_pool if is_float else self.int_reg_pool
        locked_regs = locked_regs or []

        for reg in self.lru_queue:
            if reg in pool and reg not in locked_regs:
                if not self.is_dirty.get(reg, False):
                    return reg

        for reg in self.lru_queue:
            if reg in pool and reg not in locked_regs:
                return reg

        for reg in pool: 
            if reg not in locked_regs: return reg
            
        raise Exception("No registers available to spill!")

    def create_machine_instruction(self, oc, s1, s2, d, original):
        if oc == OpCode.ADD: return Add(s1, s2, d)
        if oc == OpCode.SUB: return Sub(s1, s2, d)
        if oc == OpCode.MUL: return Mul(s1, s2, d)
        if oc == OpCode.DIV: return Div(s1, s2, d)
        if oc == OpCode.NEG: return Neg(s1, d)
        
        if oc == OpCode.FADDS: return FAdd(s1, s2, d)
        if oc == OpCode.FSUBS: return FSub(s1, s2, d)
        if oc == OpCode.FMULS: return FMul(s1, s2, d)
        if oc == OpCode.FDIVS: return FDiv(s1, s2, d)
        if oc == OpCode.FNEGS: return FNeg(s1, d)

        if oc == OpCode.MV:   return Mv(s1, d)
        if oc == OpCode.FMVS: return FMv(s1, d)
        
        if oc == OpCode.LI:    return Li(d, original.label)
        if oc == OpCode.FIMMS: return FImm(d, original.label)
        if oc == OpCode.LA:    return La(d, original.label)

        if oc == OpCode.GETI: return GetI(d)
        if oc == OpCode.GETF: return GetF(d)
        if oc == OpCode.PUTI: return PutI(s1)
        if oc == OpCode.PUTF: return PutF(s1)
        if oc == OpCode.PUTS: return PutS(s1)

        return None
        
    def expand_branch_with_allocation(self, instr, out: InstructionList):
        oc = instr.getOC()
        src1 = instr.src1
        src2 = instr.src2
        label = instr.label
        
        op_type = self.get_operand_type(src1)
        is_float = (op_type == Scope.Type.FLOAT)
        
        if not is_float:
            r1 = self.ensure(src1, out, for_writing=False, is_float_hint=False)
            r2 = self.ensure(src2, out, for_writing=False, is_float_hint=False)
            br = InstructionBranch(r1, r2, label)
            br.oc = oc
            out.append(br)
        else:
            f1 = self.ensure(src1, out, for_writing=False, is_float_hint=True)
            f2 = self.ensure(src2, out, for_writing=False, is_float_hint=True)
            cmp_reg = self.INT_SCRATCH_REGS[0]
            
            if oc == OpCode.BLT:
                out.append(Flt(f1, f2, cmp_reg))
                out.append(Bne(cmp_reg, "x0", label))
            elif oc == OpCode.BLE:
                out.append(Fle(f1, f2, cmp_reg))
                out.append(Bne(cmp_reg, "x0", label))
            elif oc == OpCode.BGT:
                out.append(Flt(f2, f1, cmp_reg))
                out.append(Bne(cmp_reg, "x0", label))
            elif oc == OpCode.BGE:
                out.append(Fle(f2, f1, cmp_reg))
                out.append(Bne(cmp_reg, "x0", label))
            elif oc == OpCode.BEQ:
                out.append(Feq(f1, f2, cmp_reg))
                out.append(Bne(cmp_reg, "x0", label))
            elif oc == OpCode.BNE:
                out.append(Feq(f1, f2, cmp_reg))
                out.append(Beq(cmp_reg, "x0", label))

    def store_reg_to_operand(self, src_reg: str, operand: str, out: InstructionList):
        is_float = src_reg.startswith('f')

        if operand.startswith('$g'):
            var_name = operand[2:]
            ste = self.global_scope.getSymbolTableEntry(var_name)
            address = ste.addressToString()

            addr_reg = self.INT_SCRATCH_REGS[1]
            out.append(La(addr_reg, address))
            if is_float:
                out.append(Fsw(src_reg, addr_reg, "0"))
            else:
                out.append(Sw(src_reg, addr_reg, "0"))

        elif operand.startswith('$l'):
            offset = operand[2:]
            if is_float:
                self.emit_ls_expanded(Fsw, src_reg, "fp", offset, out)
            else:
                self.emit_ls_expanded(Sw, src_reg, "fp", offset, out)
        
        elif operand.startswith('$t') or operand.startswith('$f'):
             offset = self.get_spill_offset(operand)
             if is_float:
                 self.emit_ls_expanded(Fsw, src_reg, "fp", str(offset), out)
             else:
                 self.emit_ls_expanded(Sw, src_reg, "fp", str(offset), out)

        elif operand == '$ret_i':
             out.append(Mv(src_reg, "a0"))
        elif operand == '$ret_f':
             out.append(FMv(src_reg, "fa0"))
        else:
            raise Exception(f"Invalid destination operand: {operand}")

    def get_spill_offset(self, temp_3ac: str) -> int:
        if temp_3ac not in self.spill_map:
            self.current_spill_offset -= 4
            self.spill_map[temp_3ac] = self.current_spill_offset
        return self.spill_map[temp_3ac]
    
    def get_operand_type(self, operand: str) -> Scope.Type:
        if operand.startswith('$f'): return Scope.Type.FLOAT
        if operand.startswith('$t'): return Scope.Type.INT
        
        if operand.startswith('$g'):
            try:
                ste = self.global_scope.getSymbolTableEntry(operand[2:])
                return ste.getType()
            except Exception:
                raise Exception(f"Could not find global symbol for {operand}")
            
        if operand.startswith('$l'):
            offset_str = operand[2:]
            for ste in self.func_scope.getEntries():
                if ste.isLocal() and str(ste.getAddress()) == offset_str:
                    return ste.getType()
            raise Exception(f"Could not find local/arg for offset {offset_str}")

        if operand == '$ret_i': return Scope.Type.INT 
        if operand == '$ret_f': return Scope.Type.FLOAT

        if '.' in operand: return Scope.Type.FLOAT
        if operand.isdigit() or (operand.startswith('-') and operand[1:].isdigit()):
            return Scope.Type.INT

        raise Exception(f"Unknown operand type: {operand}")