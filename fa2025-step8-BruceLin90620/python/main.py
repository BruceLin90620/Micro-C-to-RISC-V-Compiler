import MicroCCompiler.compiler.Compiler
import sys

# MicroCCompiler.compiler.Compiler.main(sys.argv[1])

regs = 32
dfa = False

args = sys.argv[1:]

if "--dfa" in args:
    dfa = True
    args.remove("--dfa")

if len(args) < 1:
    print("Usage: python3 python/main.py <input_file> [<num_registers>] [--dfa]", file=sys.stderr)
    sys.exit(1)

if len(args) > 1:
    try:
        regs = int(args[1])
    except ValueError:
        print(f"Invalid register count '{args[1]}', using default {regs}.", file=sys.stderr)
        pass 

MicroCCompiler.compiler.Compiler.main(args[0], regs, dfa)