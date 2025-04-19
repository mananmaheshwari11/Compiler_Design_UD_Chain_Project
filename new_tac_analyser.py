
class TACAnalyzer:
   
    def __init__(self, input_tac):
        self.input_tac = input_tac
        self.leaders = []
        self.blocks = {}
        self.successors = {}
        self.predecessors = {}
        self.dominators = {}
        self.back_edges = []
        self.loops = {}
        self.gen = {}
        self.kill = {}
        self.in_sets = {}
        self.out_sets = {}
        self.stmt_to_block = {}
        self.definitions = {}
        self.uses = {}
        self.ud_chains = {}
        self.loop_invariants = []
        self.movable_instructions = []
        self.loop_blocks = set()

    def identify_leaders(self):
        self.leaders = []
        self.leaders.append(1)  
        
        for i in range(1, len(self.input_tac)):
            if "GOTO" in self.input_tac[i]:
                target = int(self.input_tac[i].split("GOTO")[1].strip().split()[0])
                self.leaders.append(target)
                
                if "If" in self.input_tac[i]:
                    self.leaders.append(i+2)
        
        self.leaders = sorted(list(set(self.leaders)))
        return self.leaders

    def form_basic_blocks(self):
        self.blocks = {}
        
        for i, leader in enumerate(self.leaders):
            block = "B" + str(i+1)
            self.blocks[block] = []
            self.blocks[block].append(leader)
            
            for j in range(leader+1, len(self.input_tac)+1):
                if j in self.leaders:
                    break
                self.blocks[block].append(j)
        
        self.stmt_to_block = {}
        for block, stmts in self.blocks.items():
            for stmt in stmts:
                self.stmt_to_block[stmt] = block
                
        return self.blocks

    def build_cfg(self):
        self.successors = {}
        self.predecessors = {}
        
        for block in self.blocks:
            self.predecessors[block] = []
            self.successors[block] = []
        
        self.predecessors['B1'] = []
        
        for block, contents in self.blocks.items():
            last_stmt = contents[-1]
            
            if "GOTO" in self.input_tac[last_stmt-1]:
                target = int(self.input_tac[last_stmt-1].split("GOTO")[1].strip().split()[0])
                
                for key, value in self.blocks.items():
                    if target in value:
                        self.successors[block].append(key)
                        self.predecessors[key].append(block)
                
                if "If" in self.input_tac[last_stmt-1]:
                    next_block = "B" + str(int(block[1:])+1)
                    if next_block in self.blocks:
                        self.successors[block].append(next_block)
                        self.predecessors[next_block].append(block)
            
            else:
                next_block = "B" + str(int(block[1:])+1)
                if next_block in self.blocks:
                    self.successors[block].append(next_block)
                    self.predecessors[next_block].append(block)
            
            self.successors[block].sort()
        
        return self.successors, self.predecessors

    def compute_dominators(self):
        self.dominators = {}
        
        for block in self.blocks:
            self.dominators[block] = set(self.blocks.keys())
        
        self.dominators['B1'] = {'B1'} 
        
        changed = True
        while changed:
            changed = False
            for block in self.blocks:
                if block == 'B1':
                    continue
                
                preds = self.predecessors.get(block, [])
                if not preds:
                    continue
                
                new_doms = set.intersection(*[self.dominators[pred] for pred in preds])
                new_doms.add(block)  
                if new_doms != self.dominators[block]:
                    self.dominators[block] = new_doms
                    changed = True
        
        return self.dominators

    def identify_back_edges(self):
        self.back_edges = []
        
        for block, succs in self.successors.items():
            for succ in succs:
                if succ in self.dominators[block]:
                    self.back_edges.append((block, succ))
        
        return self.back_edges

    def identify_loops(self):
        self.loops = {}
        
        for tail, header in self.back_edges:
            loop = set()
            stack = [tail]
            
            while stack:
                node = stack.pop()
                if node not in loop:
                    loop.add(node)
                    for pred in self.predecessors.get(node, []):
                        if pred != header:
                            stack.append(pred)
            
            loop.add(header)
            loop_list = sorted(list(loop))
            self.loops[(header, tail)] = loop_list
            
            if header not in loop_list:
                self.loops[(header, tail)].append(header)
        
        self.loop_blocks = set()
        for loop in self.loops.values():
            self.loop_blocks.update(loop)
            
        return self.loops

    def _extract_operands(self, stmt):
        if "=" not in stmt or stmt.startswith("If"):
            return []
        
        _, rhs = stmt.split("=", 1)
        operands = [op for op in rhs.replace("[", " ").replace("]", " ").split() 
                   if op.isidentifier()]
        return operands

    def compute_gen_kill(self):
        """Compute GEN and KILL sets for each block."""

        self.gen = {block: set() for block in self.blocks}
        self.kill = {block: set() for block in self.blocks}
        self.definitions = {}
        self.uses = {}  

        for block, stmts in self.blocks.items():
            for stmt in stmts:
                var = self._get_variable(stmt)
                if var:
                    self.definitions[stmt] = var
                    
                stmt_text = self.input_tac[stmt-1]
                operands = self._extract_operands(stmt_text)
                for op in operands:
                    if op not in self.uses:
                        self.uses[op] = []
                    self.uses[op].append(stmt)
        
        for block, stmts in self.blocks.items():
            seen_vars = set()
            for stmt in stmts:
                var = self._get_variable(stmt)
                if var:
                    self.gen[block].add(stmt)
                    for prev_stmt, prev_var in self.definitions.items():
                        if prev_var == var and prev_stmt != stmt:
                            self.kill[block].add(prev_stmt)
        
        return self.gen, self.kill

    def compute_in_out(self):

        self.in_sets = {block: set() for block in self.blocks}
        self.out_sets = {block: set() for block in self.blocks}
        
        changed = True
        while changed:
            changed = False
            for block in self.blocks:
                old_in = self.in_sets[block].copy()
                old_out = self.out_sets[block].copy()
                
                if self.predecessors[block]:
                    pred_out_sets = [self.out_sets[pred] for pred in self.predecessors[block]]
                    if pred_out_sets:
                        self.in_sets[block] = set.union(*pred_out_sets) if pred_out_sets else set()
                    else:
                        self.in_sets[block] = set()
                else:
                    self.in_sets[block] = set()
                
                self.out_sets[block] = self.gen[block] | (self.in_sets[block] - self.kill[block])
                
                if old_in != self.in_sets[block] or old_out != self.out_sets[block]:
                    changed = True
        
        return self.in_sets, self.out_sets

    def compute_ud_chains(self):
        self.ud_chains = {}
        
        for var, use_stmts in self.uses.items():
            for use_stmt in use_stmts:
                if use_stmt not in self.ud_chains:
                    self.ud_chains[use_stmt] = {}
                
                self.ud_chains[use_stmt][var] = []
                use_block = self.stmt_to_block[use_stmt]
                
                reaching_defs = self.in_sets[use_block].copy()
                
                block_stmts = self.blocks[use_block]
                idx = block_stmts.index(use_stmt)
                for stmt in block_stmts[:idx]:
                    if stmt in self.definitions and self.definitions[stmt] == var:
                        for def_stmt in list(reaching_defs):
                            if self.definitions.get(def_stmt) == var:
                                reaching_defs.remove(def_stmt)
                        reaching_defs.add(stmt)
                
                for def_stmt in reaching_defs:
                    if def_stmt in self.definitions and self.definitions[def_stmt] == var:
                        self.ud_chains[use_stmt][var].append(def_stmt)
        
        return self.ud_chains

    def identify_loop_invariants(self):
        """
        Identify loop-invariant computations using UD-chains.
        A statement is loop-invariant if all its operands are:
        1. Constants
        2. Defined outside the loop
        3. Defined exactly once inside the loop but the definition is loop-invariant
        """
        self.loop_invariants = []
        
        loop_statements = []
        for block in self.loop_blocks:
            loop_statements.extend(self.blocks[block])
        
        loop_statements.sort()
        
        changed = True
        while changed:
            changed = False
            for stmt_num in loop_statements:
                if stmt_num in self.loop_invariants:
                    continue  
                
                stmt = self.input_tac[stmt_num - 1]
                if "=" not in stmt or stmt.startswith("If"):
                    continue  
                
                lhs = self._get_variable(stmt_num)
                operands = self._extract_operands(stmt)
                
                if not operands:  
                    self.loop_invariants.append(stmt_num)
                    changed = True
                    continue
                
                all_invariant = True
                
                for op in operands:
                    if stmt_num in self.ud_chains and op in self.ud_chains[stmt_num]:
                        defs = self.ud_chains[stmt_num][op]
                    else:
                        all_invariant = False
                        break
                    
                    op_invariant = True
                    for def_stmt in defs:
                        def_block = self.stmt_to_block.get(def_stmt) 
                        if def_block in self.loop_blocks and def_stmt not in self.loop_invariants:
                            op_invariant = False
                            break
                    
                    if not op_invariant:
                        all_invariant = False
                        break
                
                if all_invariant:
                    self.loop_invariants.append(stmt_num)
                    changed = True
        
        return self.loop_invariants

    def identify_movable_invariants(self):
        self.movable_instructions = []
        
        loop_exits = set()
        for block in self.loop_blocks:
            for succ in self.successors[block]:
                if succ not in self.loop_blocks:
                    loop_exits.add(succ)
        
        for stmt_num in self.loop_invariants:
            lhs = self.definitions[stmt_num]
            def_block = self.stmt_to_block[stmt_num]
            
            dominates_exits = all(def_block in self.dominators[exit_block] for exit_block in loop_exits)
            
            other_defs_in_loop = [s for s in self.definitions 
                                 if self.definitions[s] == lhs 
                                 and s != stmt_num 
                                 and self.stmt_to_block[s] in self.loop_blocks]
            if other_defs_in_loop:
                continue
                
            uses_in_loop = [use for use in self.uses.get(lhs, []) 
                           if self.stmt_to_block[use] in self.loop_blocks]
            
            all_uses_reached_by_this_def = True
            for use in uses_in_loop:
                if use in self.ud_chains and lhs in self.ud_chains[use]:
                    reaching_defs = self.ud_chains[use][lhs]
                    if not (len(reaching_defs) == 1 and stmt_num in reaching_defs):
                        all_uses_reached_by_this_def = False
                        break
            
            if all_uses_reached_by_this_def:
                self.movable_instructions.append(stmt_num)
        
        return self.movable_instructions

    def _get_variable(self, stmt_num):
        if stmt_num > len(self.input_tac):
            return None
            
        stmt = self.input_tac[stmt_num-1]
        if "=" in stmt and not stmt.startswith("If"):
            return stmt.split("=")[0].strip()
        return None

    def run_full_analysis(self):
        self.identify_leaders()
        self.form_basic_blocks()
        self.build_cfg()
        self.compute_dominators()
        self.identify_back_edges()
        self.identify_loops()
        self.compute_gen_kill()
        self.compute_in_out()
        self.compute_ud_chains()
        self.identify_loop_invariants()
        self.identify_movable_invariants()
        
        return {
            'leaders': self.leaders,
            'blocks': self.blocks,
            'successors': self.successors,
            'predecessors': self.predecessors,
            'dominators': self.dominators,
            'back_edges': self.back_edges,
            'loops': self.loops,
            'loop_blocks': self.loop_blocks,
            'gen': self.gen,
            'kill': self.kill,
            'in_sets': self.in_sets,
            'out_sets': self.out_sets,
            'ud_chains': self.ud_chains,
            'loop_invariants': self.loop_invariants,
            'movable_instructions': self.movable_instructions
        }


