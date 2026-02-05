; Symbol table 
; Function: Type.INT add([<Type.INT: 2>, <Type.INT: 2>])
; Function: Type.INT sub([<Type.INT: 2>, <Type.INT: 2>])
; Function: Type.INT mult([<Type.INT: 2>, <Type.INT: 2>])
; Function: Type.INT main([])
; Symbol table add
; name a1 type Type.INT location 12
; name a0 type Type.INT location 16
; Symbol table sub
; name a1 type Type.INT location 12
; name a0 type Type.INT location 16
; Symbol table mult
; name a1 type Type.INT location 12
; name a0 type Type.INT location 16
; Symbol table main
; name x0 type Type.INT location -4
; name x1 type Type.INT location -8
; name x2 type Type.INT location -12
; name x3 type Type.INT location -16
; name x4 type Type.INT location -20
; name x5 type Type.INT location -24
.section .text
;Current temp: 
;IR Code: 
MV fp, sp
JR func_main
HALT
;
func_add:
ADDI sp, sp, -32
SW ra, 24(sp)
SW fp, 20(sp)
ADDI fp, sp, 20
;Saving registers
SW x5, -4(fp)
SW x6, -8(fp)
SW x7, -12(fp)
;
LW x5, 16(fp)
LW x6, 12(fp)
ADD x7, x5, x6
MV a0, x7
J func_ret_add
func_ret_add:
;Restore registers
LW x5, -4(fp)
LW x6, -8(fp)
LW x7, -12(fp)
LW ra, 4(fp)
LW fp, 0(fp)
ADDI sp, sp, 32
RET
;
func_sub:
ADDI sp, sp, -32
SW ra, 24(sp)
SW fp, 20(sp)
ADDI fp, sp, 20
;Saving registers
SW x5, -4(fp)
SW x6, -8(fp)
SW x7, -12(fp)
;
LW x5, 16(fp)
LW x6, 12(fp)
SUB x7, x5, x6
MV a0, x7
J func_ret_sub
func_ret_sub:
;Restore registers
LW x5, -4(fp)
LW x6, -8(fp)
LW x7, -12(fp)
LW ra, 4(fp)
LW fp, 0(fp)
ADDI sp, sp, 32
RET
;
func_mult:
ADDI sp, sp, -32
SW ra, 24(sp)
SW fp, 20(sp)
ADDI fp, sp, 20
;Saving registers
SW x5, -4(fp)
SW x6, -8(fp)
SW x7, -12(fp)
;
LW x5, 16(fp)
LW x6, 12(fp)
MUL x7, x5, x6
MV a0, x7
J func_ret_mult
func_ret_mult:
;Restore registers
LW x5, -4(fp)
LW x6, -8(fp)
LW x7, -12(fp)
LW ra, 4(fp)
LW fp, 0(fp)
ADDI sp, sp, 32
RET
;
func_main:
ADDI sp, sp, -64
SW ra, 56(sp)
SW fp, 52(sp)
ADDI fp, sp, 52
;Saving registers
SW x5, -40(fp)
SW x6, -44(fp)
SW x7, -48(fp)
SW x9, -52(fp)
;
LI x5, 5
LI x6, 10
LI x7, 15
LI x9, 15
ADDI sp, sp, -8
ADDI sp, sp, -8
ADDI sp, sp, -4
SW x6, 0(sp)
ADDI sp, sp, -4
SW x6, 0(sp)
SW x5, -4(fp)
SW x6, -8(fp)
SW x7, -12(fp)
SW x9, -16(fp)
JR func_sub
MV x5, a0
MV x6, x5
ADDI sp, sp, 16
ADDI sp, sp, -4
SW x6, 0(sp)
ADDI sp, sp, -8
LW x6, -12(fp)
ADDI sp, sp, -4
SW x6, 0(sp)
LW x7, -16(fp)
ADDI sp, sp, -4
SW x7, 0(sp)
JR func_mult
MV x5, a0
MV x6, x5
ADDI sp, sp, 16
ADDI sp, sp, -4
SW x6, 0(sp)
SW x6, -28(fp)
JR func_add
MV x5, a0
MV x6, x5
ADDI sp, sp, 16
ADDI sp, sp, -8
ADDI sp, sp, -8
LW x6, -12(fp)
ADDI sp, sp, -4
SW x6, 0(sp)
LW x7, -16(fp)
ADDI sp, sp, -4
SW x7, 0(sp)
JR func_mult
MV x5, a0
MV x6, x5
ADDI sp, sp, 16
ADDI sp, sp, -4
SW x6, 0(sp)
ADDI sp, sp, -8
LW x6, -12(fp)
ADDI sp, sp, -4
SW x6, 0(sp)
LW x7, -16(fp)
ADDI sp, sp, -4
SW x7, 0(sp)
JR func_add
MV x5, a0
MV x6, x5
ADDI sp, sp, 16
ADDI sp, sp, -4
SW x6, 0(sp)
SW x6, -32(fp)
JR func_sub
MV x5, a0
MV x6, x5
ADDI sp, sp, 16
LW x7, -36(fp)
ADD x9, x7, x6
LI x6, 1
ADD x7, x9, x6
PUTI x7
SW x7, -24(fp)
func_ret_main:
;Restore registers
LW x5, -40(fp)
LW x6, -44(fp)
LW x7, -48(fp)
LW x9, -52(fp)
LW ra, 4(fp)
LW fp, 0(fp)
ADDI sp, sp, 64
RET
;

.section .strings
