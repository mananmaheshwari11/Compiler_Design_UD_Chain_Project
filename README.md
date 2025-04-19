# Compiler_Design_UD_Chain_Project

#Problem Definition:
The problem is to identify and move loop invariant statements outside the loop to optimize the code and reduce redundant computations. Loop invariant computation plays a vital role in compiler optimizations for enhancing execution speed and reducing instruction overhead in loops.
#Solution Description:
To solve the problem, we first identify leader statements and divide the code into basic blocks. These basic blocks are used to construct a control flow graph (CFG). Using the CFG, we determine dominators of each block, identify backedges to detect loops, and classify loop regions. For each statement, we calculate GEN, KILL, IN, and OUT sets which are used to build Use-Definition (UD) chains. Based on these UD chains and dominance relations, we find loop invariant statements and move them to a newly created pre-header block outside the loop to achieve code optimization. The graphical view of the CFG before and after optimization is displayed as output.

![image](https://github.com/user-attachments/assets/981e68f8-81fb-4948-b609-bee28d710d86)
![image](https://github.com/user-attachments/assets/a2725b70-a4a3-47e1-9afa-2ff643fc1b37)
![image](https://github.com/user-attachments/assets/9f40f027-7e92-4b90-993e-c0c890753137)
