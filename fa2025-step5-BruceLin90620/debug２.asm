; Symbol table 
; Function: Type.INT foo([<Type.INT: 2>, <Type.INT: 2>])
; Function: Type.INT bar([<Type.INT: 2>, <Type.INT: 2>])
; Function: Type.INT main([])
; Symbol table main
; name a type Type.INT location -4
; name b type Type.INT location -8
; name c type Type.INT location -12
; name d type Type.INT location -16
; Symbol table foo
; name y type Type.INT location 12
; name x type Type.INT location 16
; Symbol table bar
; name y type Type.INT location 12
; name x type Type.INT location 16
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
SW x11, -20(fp)
SW x5, -24(fp)
SW x6, -28(fp)
SW x7, -32(fp)
SW x9, -36(fp)
;
GETI x5
GETI x6
ADDI sp, sp, -4
SW x5, 0(sp)
ADDI sp, sp, -4
SW x6, 0(sp)
SW x5, -4(fp)
SW x6, -8(fp)
JR func_foo
MV x5, a0
MV x6, x5
ADDI sp, sp, 8
MV x7, x6
LW x9, -4(fp)
ADDI sp, sp, -4
SW x9, 0(sp)
LW x11, -8(fp)
ADDI sp, sp, -4
SW x11, 0(sp)
SW x7, -12(fp)
JR func_bar
MV x5, a0
MV x6, x5
ADDI sp, sp, 8
MV x7, x6
LW x9, -12(fp)
PUTI x9
PUTI x7
LI x11, 0
MV x5, x11
MV a0, x5
SW x7, -16(fp)
J func_ret_main
func_ret_main:
;Restore registers
LW x11, -20(fp)
LW x5, -24(fp)
LW x6, -28(fp)
LW x7, -32(fp)
LW x9, -36(fp)
LW ra, 4(fp)
LW fp, 0(fp)
ADDI sp, sp, 48
RET
;
func_foo:
ADDI sp, sp, -32
SW ra, 24(sp)
SW fp, 20(sp)
ADDI fp, sp, 20
;Saving registers
SW x5, -4(fp)
SW x6, -8(fp)
SW x7, -12(fp)
SW x9, -16(fp)
;
LW x5, 16(fp)
LW x6, 12(fp)
ADD x7, x5, x6
MV x9, x7
MV a0, x9
J func_ret_foo
func_ret_foo:
;Restore registers
LW x5, -4(fp)
LW x6, -8(fp)
LW x7, -12(fp)
LW x9, -16(fp)
LW ra, 4(fp)
LW fp, 0(fp)
ADDI sp, sp, 32
RET
;
func_bar:
ADDI sp, sp, -32
SW ra, 24(sp)
SW fp, 20(sp)
ADDI fp, sp, 20
;Saving registers
SW x5, -4(fp)
SW x6, -8(fp)
SW x7, -12(fp)
SW x9, -16(fp)
;
LW x5, 16(fp)
LW x6, 12(fp)
SUB x7, x5, x6
MV x9, x7
MV a0, x9
J func_ret_bar
func_ret_bar:
;Restore registers
LW x5, -4(fp)
LW x6, -8(fp)
LW x7, -12(fp)
LW x9, -16(fp)
LW ra, 4(fp)
LW fp, 0(fp)
ADDI sp, sp, 32
RET
;

.section .strings
