; Symbol table 
; name a type Type.FLOAT location 0x20000000
; name b type Type.FLOAT location 0x20000004
; name c type Type.FLOAT location 0x20000008
; name d type Type.FLOAT location 0x2000000c
; name prompt type Type.STRING location 0x10000000 value "Enter a number: "
; Function: Type.INT main([])
; Symbol table main
.section .text
;Current temp: 
;IR Code: 
MV fp, sp
JR func_main
HALT
;
func_main:
ADDI sp, sp, -8
SW ra, 4(sp)
SW fp, 0(sp)
ADDI fp, sp, 0
FIMM.S f2, 1.3
FMV.S f0 f2
LA t1, 0x20000000
FSW f0, 0(t1)
FIMM.S f3, 2.5
FMV.S f0 f3
LA t1, 0x20000004
FSW f0, 0(t1)
LA t0, 0x10000000
PUTS t0
GETF f0
LA t1, 0x20000008
FSW f0, 0(t1)
LA t1, 0x20000004
FLW f0, 0(t1)
LA t1, 0x20000008
FLW f1, 0(t1)
FMUL.S f4, f0, f1
LA t1, 0x20000000
FLW f0, 0(t1)
FMV.S f1 f4
FADD.S f5, f0, f1
FMV.S f0 f5
PUTF f0
LI t2, 0
MV t0, t2
MV a0, t0
J func_ret_main
func_ret_main:
LW ra, 4(fp)
LW fp, 0(fp)
ADDI sp, sp, 8
RET
;

.section .strings
0x10000000 "Enter a number: "
