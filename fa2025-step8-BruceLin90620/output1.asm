; Symbol table 
; name curVal type Type.FLOAT location 0x20000000
; name x type Type.FLOAT location 0x20000004
; name degree type Type.INT location 0x20000008
; Function: Type.FLOAT poly([<Type.FLOAT: 3>, <Type.FLOAT: 3>, <Type.INT: 2>])
; name val type Type.STRING location 0x10000000 value "Enter x value to evaluate: "
; name degreePrompt type Type.STRING location 0x10000004 value "Enter a degree: "
; name prompt type Type.STRING location 0x10000008 value "Enter coefficient: "
; Function: Type.INT main([])
; Symbol table main
; name cur type Type.INT location -4
; Symbol table poly
; name degree type Type.INT location 12
; name x type Type.FLOAT location 16
; name curVal type Type.FLOAT location 20
; name coeff type Type.FLOAT location -4
DEBUG postprocessCondNode: co.temp=('$l12', '$t0', <OpType.GT: 5>, <Type.INT: 2>)
.section .text
;Current temp: 
;IR Code: 
MV fp, sp
JR func_main
HALT
;
func_main:
ADDI sp, sp, -48
SW ra, 40(sp)
SW fp, 36(sp)
ADDI fp, sp, 36
;Saving registers
SW x5, -8(fp)
SW x6, -12(fp)
SW x7, -16(fp)
SW x9, -20(fp)
FSW f2, -24(fp)
FSW f3, -28(fp)
;
FIMM.S f2, 0.0
LI x5, 0
LA x6, 0x10000000
PUTS x6
GETF f3
LA x7, 0x10000004
PUTS x7
GETI x9
ADDI sp, sp, -4
FSW f2, 0(sp)
ADDI sp, sp, -4
FSW f3, 0(sp)
ADDI sp, sp, -4
SW x9, 0(sp)
LA x4, 0x20000000
FSW f2, 0(x4)
SW x5, -4(fp)
LA x4, 0x20000004
FSW f3, 0(x4)
LA x4, 0x20000008
SW x9, 0(x4)
JR func_poly
FMV.S f2, fa0
FMV.S f3, f2
ADDI sp, sp, 12
PUTF f3
LI x5, 0
LA x4, 0x20000000
FSW f3, 0(x4)
MV a0, x5
J func_ret_main
func_ret_main:
;Restore registers
LW x5, -8(fp)
LW x6, -12(fp)
LW x7, -16(fp)
LW x9, -20(fp)
FLW f2, -24(fp)
FLW f3, -28(fp)
LW ra, 4(fp)
LW fp, 0(fp)
ADDI sp, sp, 48
RET
;
func_poly:
ADDI sp, sp, -64
SW ra, 56(sp)
SW fp, 52(sp)
ADDI fp, sp, 52
;Saving registers
SW x5, -16(fp)
SW x6, -20(fp)
SW x7, -24(fp)
FSW f2, -28(fp)
FSW f3, -32(fp)
FSW f4, -36(fp)
FSW f5, -40(fp)
FSW f6, -44(fp)
;
LI x5, 0
LW x6, 12(fp)
SW x5, -8(fp)
BLE x6, x5, else_1
FLW f2, 20(fp)
ADDI sp, sp, -4
FSW f2, 0(sp)
FLW f3, 16(fp)
ADDI sp, sp, -4
FSW f3, 0(sp)
LI x5, 1
LW x6, 12(fp)
SUB x7, x6, x5
ADDI sp, sp, -4
SW x7, 0(sp)
SW x7, -12(fp)
JR func_poly
FMV.S f2, fa0
FMV.S f3, f2
ADDI sp, sp, 12
FSW f3, 20(fp)
J out_1
else_1:
out_1:
LA x5, 0x10000008
PUTS x5
GETF f2
FLW f3, 16(fp)
FLW f4, 20(fp)
FMUL.S f5, f3, f4
FADD.S f6, f5, f2
FSW f2, -4(fp)
FMV.S fa0, f6
J func_ret_poly
func_ret_poly:
;Restore registers
LW x5, -16(fp)
LW x6, -20(fp)
LW x7, -24(fp)
FLW f2, -28(fp)
FLW f3, -32(fp)
FLW f4, -36(fp)
FLW f5, -40(fp)
FLW f6, -44(fp)
LW ra, 4(fp)
LW fp, 0(fp)
ADDI sp, sp, 64
RET
;

.section .strings
0x10000000 "Enter x value to evaluate: "
0x10000004 "Enter a degree: "
0x10000008 "Enter coefficient: "
