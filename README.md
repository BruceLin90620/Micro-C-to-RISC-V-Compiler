# Micro-C to RISC-V Compiler

This repository contains programming assignments, focusing on the incremental development of a multi-stage compiler that translates Micro-C into RISC-V assembly code.

## 📝 Project Highlights

### Steps 1 - 3: Lexical Analysis & AST Construction

* **Scanner & Parser**: Leveraged **ANTLR4** to define the Micro-C grammar, implementing robust lexical analysis and parse tree generation.
* **Symbol Table**: Developed a scoped symbol table manager to handle variable declarations, type tracking, and nested scope resolution.
* **Abstract Syntax Tree (AST)**: Built a comprehensive AST framework to transform raw parse trees into structured representations for semantic analysis.

### Steps 4 - 6: Intermediate Logic & Control Flow

* **Code Generation backend**: Implemented a backend engine to map AST nodes directly to **RISC-V ISA** instructions.
* **Control Structures**: Added support for conditional branching (`if-else`) and iterative logic (`while` loops) using automated label generation.
* **Function Support**: Engineered the calling convention infrastructure, including stack frame management, parameter passing, and return address handling.

### Steps 7 - 8: Memory Abstraction & Advanced Features

* **Pointers & Arrays**: Implemented pointer arithmetic, address-of (`&`) operations, and dereferencing (`*`) logic.
* **Dynamic Memory**: Integrated support for heap-based operations including `malloc` and `free` abstractions.
* **Backend Optimization**: Refined register allocation and assembly emission to ensure full compatibility with the **RiscSim** and Spike simulators.
