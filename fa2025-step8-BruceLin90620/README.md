[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/vEJ4abY6)
# Step 8: More Optimizations
## Due: Dec 5th, 5 pm EST (10 pm UTC)


## Setting up your repository


Set up your GitHub classroom repository for step 8 using the link in Piazza.


Set up your project development and testing environment as mentioned in the [project environment documentations](https://cap.ecn.purdue.edu/compilers/project/).


Then clone your repository as directed in the cloning and submitting instructions.


## Background


In this step we are going to test various other compiler optimizations which play a crucial role in real compilers.


There is no starter code for this assignment. You may choose to start with your Step 7 code. If your step 7 is not ready, Step 6 could be used instead. If Step 6 is also not ready, Step 4 could be taken as the starting point. (Use the most full fledged compiler you may have.)


We encourage you to start working on this project ASAP, and may chat with us over Piazza or during office hours to get some
guidance on how to implement the various pieces of the project. You should also refer to the steps we took to add
new features to our language in previous project steps as a roadmap.


## The following optimizations may be considered
1. Constant Folding
1. Algebraic Simplification
1. Loop-invariant Code Motion
1. Loop Elimination
1. Inlining Functions
1. Inlining Recursive Functions
1. Tail Call Elimination


## Grading and Hidden tests


For this step, we will consider all test cases as hidden for all submissions. The test cases are not included in the repo, but will
be added to the grader and will be included in the grader results. All hidden test cases will be used for checking correctness and performance.


The number of instruction cycles executed during the simulation run (Note that this means the actual runtime count, not the count in the asm file) will be collected for both your assembly output (denoted as S) and the reference output (denoted as R). Then, your credits for this particular test would be adjusted as follows:
```
60% * (If test passes) + 40% * min ( 25%, max ( 1 - S/R, 0))/25%
```


These hidden tests are designed to test against all previous step implementations. These include excessive code that is meant to stress-test your compiler to make sure that in edge cases it still behaves correctly.


Credits for each test case are distributed evenly. After adjustment of performance, the credits will be accumulated together to reflect your total grades. Then for the late submission penalties, if any, will be applied to produce your final grades for the step.


For this step, considering the difficult nature of the assignment, we may curve the grades from the grader (based on grades distribution) after grading has been concluded. Then curved grades will be uploaded to BrightSpace.


## What you need to submit


* All of the necessary code for building your compiler.


* A Makefile with the following targets:
    1. `compiler`: this target will build your compiler
    2. `clean`: this target will remove any intermediate files that were created to build the compiler


* A shell script (this *must* be written in bash, which is located at `/bin/bash` on the ecegrid machines) called `runme` that runs your scanner. This script should take in two arguments: first, the input file to the compiler  and second, the filename where you want to put the compiler's output. You can assume that we will have run `make clean; make compiler` before running this script, and that we will invoke the script from the root directory of your compiler.


While you may create as many other directories as you would like to organize your code or any intermediate products of the compilation process, both your `Makefile` and your `runme` script should be in the root directory of your repository.

*Do not submit any binaries*. Your git repo should only contain source files; no products of compilation.

See the Piazza post for instructions on how to submit your assignment to Gradescope.
