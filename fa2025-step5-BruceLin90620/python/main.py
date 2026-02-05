import MicroCCompiler.compiler.Compiler
import sys

# MicroCCompiler.compiler.Compiler.main(sys.argv[1])

# 預設暫存器數量為 32
regs = 32
if len(sys.argv) > 2:
    try:
        # 從 sys.argv[2] 讀取暫存器數量
        regs = int(sys.argv[2])
    except ValueError:
        print(f"Invalid register count '{sys.argv[2]}', using default {regs}.", file=sys.stderr)
        pass # 保持預設值

if len(sys.argv) < 2:
    print("Usage: python3 python/main.py <input_file> [<num_registers>]", file=sys.stderr)
    sys.exit(1)

# 將檔名和暫存器數量都傳遞給 Compiler.main
MicroCCompiler.compiler.Compiler.main(sys.argv[1], regs)