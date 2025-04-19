#!/usr/bin/env python3
# new_tac_visualization.py - Improved TAC Visualization with UD-Chains

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import networkx as nx
import numpy as np
import pandas as pd
from matplotlib.table import Table
from new_tac_analyser import TACAnalyzer
import matplotlib
matplotlib.use('TkAgg')  # Use TkAgg backend for matplotlib

class TACVisualization:
    """
    A class for visualizing Three Address Code analysis and loop-invariant code motion.
    """
    def __init__(self, root, input_tac=None):
        """Initialize the visualization."""
        self.root = root
        self.root.title("Three Address Code Analyzer")
        self.root.geometry("1280x900")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Default example code
        if input_tac is None:
            self.input_tac = [
                "sum = 0", 
                "i = 0", 
                "If i > n GOTO 12", 
                "t1 = 0", 
                "t2 = i * 4",
                "t3 = t1[t2]",
                "t4 = sum + t3",
                "sum = t4",
                "t5 = i + 1",
                "i = t5",
                "GOTO 3", 
                "return sum"
            ]
        else:
            self.input_tac = input_tac
        
        # Create the analyzer object
        self.analyzer = TACAnalyzer(self.input_tac)
        
        # State variables
        self.current_step = 0
        self.steps = [
            "Introduction",
            "Leader Statements",
            "Basic Blocks",
            "Control Flow Graph",
            "Dominators",
            "Back Edges",
            "Natural Loops",
            "Data Flow Analysis",
            "Loop-Invariant Code",
            "Code Motion"
        ]
        self.highlighted_stmts = []
        self.highlighted_blocks = []
        self.selected_block = None
        
        # Set up UI
        self.setup_ui()
        self.update_display()
        
    def setup_ui(self):
        """Set up the user interface."""
        # Set up frames
        self.main_panel = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_panel.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel for code and controls
        self.left_panel = ttk.Frame(self.main_panel)
        self.main_panel.add(self.left_panel, weight=1)
        
        # Right panel with tabs
        self.right_panel = ttk.Frame(self.main_panel)
        self.main_panel.add(self.right_panel, weight=2)
        
        # Configure tab control
        self.tab_control = ttk.Notebook(self.right_panel)
        self.tab_control.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.graph_tab = ttk.Frame(self.tab_control)
        self.table_tab = ttk.Frame(self.tab_control)
        self.ud_tab = ttk.Frame(self.tab_control)  # New tab for UD-chains
        self.info_tab = ttk.Frame(self.tab_control)
        
        self.tab_control.add(self.graph_tab, text="Control Flow Graph")
        self.tab_control.add(self.table_tab, text="Data Flow Tables")
        self.tab_control.add(self.ud_tab, text="Use-Definition Chains")  # Add new tab
        self.tab_control.add(self.info_tab, text="Detailed Info")
        
        # Set up graph display in first tab
        self.setup_graph_display()
        
        # Set up table display in second tab
        self.setup_table_display()
        
        # Set up UD chains display in third tab
        self.setup_ud_display()
        
        # Set up detailed info in fourth tab
        self.setup_info_display()
        
        # Set up code display on left panel
        self.setup_code_display()
        
        # Set up controls
        self.setup_controls()

        # Set up explanation area
        self.setup_explanation()
        
    def setup_graph_display(self):
        """Set up the graph visualization area."""
        self.graph_frame = ttk.Frame(self.graph_tab)
        self.graph_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create figure and axes for the graph
        self.fig = plt.Figure(figsize=(8, 6), tight_layout=True)
        self.ax = self.fig.add_subplot(111)
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Control area for the graph
        self.graph_control_frame = ttk.Frame(self.graph_tab)
        self.graph_control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Block details area
        self.block_details_frame = ttk.LabelFrame(self.graph_tab, text="Block Details")
        self.block_details_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.block_details_text = scrolledtext.ScrolledText(self.block_details_frame, wrap=tk.WORD, height=5)
        self.block_details_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def setup_table_display(self):
        """Set up the table visualization area."""
        # Create paned window for top and bottom tables
        self.table_panel = ttk.PanedWindow(self.table_tab, orient=tk.VERTICAL)
        self.table_panel.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Top frame for GEN/KILL tables
        self.top_table_frame = ttk.LabelFrame(self.table_panel, text="GEN/KILL Sets")
        self.table_panel.add(self.top_table_frame, weight=1)
        
        # Bottom frame for IN/OUT tables
        self.bottom_table_frame = ttk.LabelFrame(self.table_panel, text="IN/OUT Sets")
        self.table_panel.add(self.bottom_table_frame, weight=1)
        
        # Create figures for tables
        self.gen_kill_fig = plt.Figure(figsize=(8, 3), tight_layout=True)
        self.gen_kill_canvas = FigureCanvasTkAgg(self.gen_kill_fig, master=self.top_table_frame)
        self.gen_kill_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.in_out_fig = plt.Figure(figsize=(8, 3), tight_layout=True)
        self.in_out_canvas = FigureCanvasTkAgg(self.in_out_fig, master=self.bottom_table_frame)
        self.in_out_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def setup_ud_display(self):
        """Set up the UD chains visualization area."""
        # Create a frame for UD chain visualization
        self.ud_scroll = scrolledtext.ScrolledText(self.ud_tab, wrap=tk.WORD)
        self.ud_scroll.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def setup_info_display(self):
        """Set up the detailed information display area."""
        self.info_scroll = scrolledtext.ScrolledText(self.info_tab, wrap=tk.WORD)
        self.info_scroll.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def setup_code_display(self):
        """Set up the code display area."""
        code_frame = ttk.LabelFrame(self.left_panel, text="Three Address Code")
        code_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.code_text = scrolledtext.ScrolledText(code_frame, wrap=tk.WORD, font=('Courier', 10))
        self.code_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure tags for highlighting
        self.code_text.tag_configure("highlight", background="yellow")
        self.code_text.tag_configure("block1", background="#FFB6C1")  # LightPink
        self.code_text.tag_configure("block2", background="#ADD8E6")  # LightBlue
        self.code_text.tag_configure("block3", background="#90EE90")  # LightGreen
        self.code_text.tag_configure("block4", background="#FFFACD")  # LemonChiffon
        self.code_text.tag_configure("block5", background="#E6E6FA")  # Lavender
        self.code_text.tag_configure("line_num", foreground="gray")
        
        # Load code
        self.update_code_display()
        
    def setup_controls(self):
        """Set up the control buttons."""
        controls_frame = ttk.Frame(self.left_panel)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.prev_button = ttk.Button(controls_frame, text="← Previous", command=self.previous_step)
        self.prev_button.grid(row=0, column=0, padx=5, pady=5)
        
        self.next_button = ttk.Button(controls_frame, text="Next →", command=self.next_step)
        self.next_button.grid(row=0, column=1, padx=5, pady=5)
        
        self.step_var = tk.StringVar()
        self.step_var.set(f"Step 1 of {len(self.steps)}: {self.steps[0]}")
        
        self.step_label = ttk.Label(controls_frame, textvariable=self.step_var)
        self.step_label.grid(row=0, column=2, padx=20, pady=5)
        
        # Add auto-play feature
        self.auto_button = ttk.Button(controls_frame, text="Auto Play", command=self.toggle_auto_play)
        self.auto_button.grid(row=0, column=3, padx=5, pady=5)
        
        self.auto_playing = False
        self.auto_delay = 2000  # milliseconds
        
    def setup_explanation(self):
        """Set up the explanation text area."""
        explanation_frame = ttk.LabelFrame(self.left_panel, text="Explanation")
        explanation_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.explanation_text = scrolledtext.ScrolledText(explanation_frame, wrap=tk.WORD, height=8)
        self.explanation_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def update_code_display(self, highlight_stmts=None, color_blocks=False):
        """Update the code display with highlighting."""
        self.code_text.config(state=tk.NORMAL)
        self.code_text.delete(1.0, tk.END)
        
        for i, line in enumerate(self.input_tac):
            line_num = i + 1
            line_text = f"{line_num}: {line}\n"
            
            # Insert with line number in gray
            self.code_text.insert(tk.END, f"{line_num}: ", "line_num")
            
            # Determine if this line should be highlighted and how
            if highlight_stmts and line_num in highlight_stmts:
                self.code_text.insert(tk.END, f"{line}\n", "highlight")
            elif color_blocks and self.current_step >= 2:
                # Find which block this statement belongs to
                block_num = None
                for block, stmts in self.analyzer.blocks.items():
                    if line_num in stmts:
                        block_num = int(block[1:])
                        break
                
                if block_num:
                    tag_name = f"block{(block_num % 5) or 5}"  # Cycle through 5 colors
                    self.code_text.insert(tk.END, f"{line}\n", tag_name)
                else:
                    self.code_text.insert(tk.END, f"{line}\n")
            else:
                self.code_text.insert(tk.END, f"{line}\n")
        
        self.code_text.config(state=tk.DISABLED)
    
    def draw_cfg(self, show_cfg=True, highlight_blocks=None, highlight_edges=None):
        """Draw the Control Flow Graph."""
        self.ax.clear()
        
        if not show_cfg or not self.analyzer.blocks:
            self.ax.text(0.5, 0.5, "Control Flow Graph will appear here\nafter basic blocks are identified.", 
                        ha='center', va='center', fontsize=12)
            self.canvas.draw()
            return
        
        # Create directed graph
        G = nx.DiGraph()
        
        # Add nodes
        for block in self.analyzer.blocks:
            G.add_node(block)
        
        # Add edges
        for block, succs in self.analyzer.successors.items():
            for succ in succs:
                G.add_edge(block, succ)
        
        # Set positions with a more structured layout
        if len(G.nodes) <= 3:
            pos = nx.spring_layout(G, seed=42)
        else:
            # Try to use a more organized layout for larger graphs
            try:
                pos = nx.planar_layout(G)
            except:
                try:
                    pos = nx.kamada_kawai_layout(G)
                except:
                    pos = nx.spring_layout(G, seed=42)
        
        # Node colors
        node_colors = ['lightblue' for _ in G.nodes]
        if highlight_blocks:
            for i, node in enumerate(G.nodes):
                if node in highlight_blocks:
                    node_colors[i] = 'yellow'
        
        # Draw nodes
        nx.draw_networkx_nodes(G, pos, node_size=700, node_color=node_colors, ax=self.ax)
        
        # Draw edges with specified arrow properties to ensure heads are visible
        regular_edges = [(u, v) for u, v in G.edges if (u, v) not in (highlight_edges or [])]
        if regular_edges:
            nx.draw_networkx_edges(
                G, pos, edgelist=regular_edges, ax=self.ax,
                arrows=True, arrowsize=20, width=1.5,
                arrowstyle='-|>', connectionstyle='arc3,rad=0.1'
            )
        
        # Draw highlighted edges
        if highlight_edges:
            nx.draw_networkx_edges(
                G, pos, edgelist=highlight_edges, ax=self.ax,
                arrows=True, arrowsize=25, width=2, 
                edge_color='red', arrowstyle='-|>', 
                connectionstyle='arc3,rad=0.1'
            )
        
        # Draw labels showing block contents
        labels = {}
        for block in G.nodes:
            stmts = self.analyzer.blocks.get(block, [])
            stmt_nums = ", ".join(map(str, stmts))
            labels[block] = f"{block}\n({stmt_nums})"
        
        nx.draw_networkx_labels(G, pos, labels=labels, font_size=9, ax=self.ax)
        
        # Set up event handling for clicking nodes
        self.fig.canvas.mpl_connect('button_press_event', self.on_graph_click)
        self.node_positions = pos  # Store positions for click detection
        
        self.ax.set_axis_off()
        self.canvas.draw()
    
    def draw_tables(self):
        """Draw data flow tables (GEN/KILL and IN/OUT)."""
        # Clear previous tables
        self.gen_kill_fig.clear()
        self.in_out_fig.clear()
        
        if self.current_step < 7:  # Tables only shown in step 7+
            self.gen_kill_fig.text(0.5, 0.5, "Data flow tables will appear here\nin step 7 (Data Flow Analysis).", 
                                 ha='center', va='center', fontsize=12)
            self.in_out_fig.text(0.5, 0.5, "Data flow tables will appear here\nin step 7 (Data Flow Analysis).", 
                                ha='center', va='center', fontsize=12)
            self.gen_kill_canvas.draw()
            self.in_out_canvas.draw()
            return
        
        # Create GEN/KILL table
        ax_gen_kill = self.gen_kill_fig.add_subplot(111)
        ax_gen_kill.set_axis_off()
        
        # Prepare data for GEN/KILL table
        blocks = list(self.analyzer.blocks.keys())
        gen_values = []
        kill_values = []
        
        for block in blocks:
            gen_values.append(', '.join(map(str, sorted(self.analyzer.gen.get(block, [])))) or '-')
            kill_values.append(', '.join(map(str, sorted(self.analyzer.kill.get(block, [])))) or '-')
        
        # Create table data
        gen_kill_data = []
        for i, block in enumerate(blocks):
            gen_kill_data.append([block, gen_values[i], kill_values[i]])
        
        # Create the table
        gen_kill_table = ax_gen_kill.table(
            cellText=gen_kill_data,
            colLabels=['Block', 'GEN', 'KILL'],
            loc='center',
            cellLoc='center',
            colWidths=[0.1, 0.45, 0.45]
        )
        
        # Styling
        gen_kill_table.auto_set_font_size(False)
        gen_kill_table.set_fontsize(10)
        gen_kill_table.scale(1, 1.5)
        
        # Color the header row
        for i in range(3):
            gen_kill_table[(0, i)].set_facecolor('#4472C4')
            gen_kill_table[(0, i)].set_text_props(color='white')
        
        # Create IN/OUT table
        ax_in_out = self.in_out_fig.add_subplot(111)
        ax_in_out.set_axis_off()
        
        # Prepare data for IN/OUT table
        in_values = []
        out_values = []
        
        for block in blocks:
            in_values.append(', '.join(map(str, sorted(self.analyzer.in_sets.get(block, [])))) or '-')
            out_values.append(', '.join(map(str, sorted(self.analyzer.out_sets.get(block, [])))) or '-')
        
        # Create table data
        in_out_data = []
        for i, block in enumerate(blocks):
            in_out_data.append([block, in_values[i], out_values[i]])
        
        # Create the table
        in_out_table = ax_in_out.table(
            cellText=in_out_data,
            colLabels=['Block', 'IN', 'OUT'],
            loc='center',
            cellLoc='center',
            colWidths=[0.1, 0.45, 0.45]
        )
        
        # Styling
        in_out_table.auto_set_font_size(False)
        in_out_table.set_fontsize(10)
        in_out_table.scale(1, 1.5)
        
        # Color the header row
        for i in range(3):
            in_out_table[(0, i)].set_facecolor('#4472C4')
            in_out_table[(0, i)].set_text_props(color='white')
        
        # Draw the tables
        self.gen_kill_canvas.draw()
        self.in_out_canvas.draw()
    
    def draw_ud_chains(self):
        """Draw the UD chains information."""
        self.ud_scroll.config(state=tk.NORMAL)
        self.ud_scroll.delete(1.0, tk.END)
        
        if not self.analyzer.ud_chains:
            if self.current_step >= 7:  # Only compute after data flow analysis
                # Generate UD chains
                self.analyzer.compute_ud_chains()
            else:
                self.ud_scroll.insert(tk.END, "UD chains will be computed after data flow analysis (step 7)")
                self.ud_scroll.config(state=tk.DISABLED)
                return
        
        # Display UD chains
        self.ud_scroll.insert(tk.END, "Use-Definition Chains\n")
        self.ud_scroll.insert(tk.END, "======================\n\n")
        self.ud_scroll.insert(tk.END, "The UD chains show, for each use of a variable, which definitions can reach that use.\n\n")
        
        # For each statement using variables
        for use_stmt in sorted(self.analyzer.ud_chains.keys()):
            if use_stmt <= len(self.input_tac):
                self.ud_scroll.insert(tk.END, f"Statement {use_stmt}: {self.input_tac[use_stmt-1]}\n")
                
                # For each variable in this statement
                for var, def_stmts in sorted(self.analyzer.ud_chains[use_stmt].items()):
                    self.ud_scroll.insert(tk.END, f"  Variable '{var}' is defined at:\n")
                    
                    # List all reaching definitions
                    for def_stmt in sorted(def_stmts):
                        if def_stmt <= len(self.input_tac):
                            self.ud_scroll.insert(tk.END, f"    Statement {def_stmt}: {self.input_tac[def_stmt-1]}\n")
                
                self.ud_scroll.insert(tk.END, "\n")
        
        self.ud_scroll.config(state=tk.DISABLED)
    
    def on_graph_click(self, event):
        """Handle clicks on the graph to select blocks."""
        if self.current_step < 3 or not hasattr(self, 'node_positions'):
            return
            
        # Find the closest node to the click
        min_dist = float('inf')
        closest_node = None
        
        for node, pos in self.node_positions.items():
            dist = np.sqrt((event.xdata - pos[0])**2 + (event.ydata - pos[1])**2)
            if dist < min_dist and dist < 0.1:  # 0.1 is the click tolerance
                min_dist = dist
                closest_node = node
        
        if closest_node:
            self.selected_block = closest_node
            self.update_block_details(closest_node)
    
    def update_block_details(self, block):
        """Update the block details text area with information about the selected block."""
        self.block_details_text.config(state=tk.NORMAL)
        self.block_details_text.delete(1.0, tk.END)
        
        if not block or block not in self.analyzer.blocks:
            self.block_details_text.config(state=tk.DISABLED)
            return
        
        # Create details text
        details = f"Block: {block}\n\n"
        
        # Statements
        stmts = self.analyzer.blocks.get(block, [])
        details += "Statements:\n"
        for stmt in stmts:
            if stmt <= len(self.input_tac):
                details += f"  {stmt}: {self.input_tac[stmt-1]}\n"
        
        details += "\n"
        
        # Successors and predecessors
        details += f"Successors: {', '.join(self.analyzer.successors.get(block, []))}\n"
        details += f"Predecessors: {', '.join(self.analyzer.predecessors.get(block, []))}\n\n"
        
        # If we're in step 4+, show dominators
        if self.current_step >= 4:
            details += f"Dominators: {', '.join(sorted(self.analyzer.dominators.get(block, [])))}\n\n"
        
        # If we're in step 7+, show data flow info
        if self.current_step >= 7:
            details += "Data Flow:\n"
            details += f"  GEN: {', '.join(map(str, sorted(self.analyzer.gen.get(block, []))))}\n"
            details += f"  KILL: {', '.join(map(str, sorted(self.analyzer.kill.get(block, []))))}\n"
            details += f"  IN: {', '.join(map(str, sorted(self.analyzer.in_sets.get(block, []))))}\n"
            details += f"  OUT: {', '.join(map(str, sorted(self.analyzer.out_sets.get(block, []))))}\n"
        
        self.block_details_text.insert(tk.END, details)
        self.block_details_text.config(state=tk.DISABLED)
    
    def update_info_display(self):
        """Update the detailed information display."""
        self.info_scroll.config(state=tk.NORMAL)
        self.info_scroll.delete(1.0, tk.END)
        
        # Different content based on current step
        if self.current_step == 0:  # Introduction
            info = """Welcome to the Three Address Code Analyzer
            
This tool helps visualize the process of analyzing Three Address Code (TAC) and identifying loop-invariant computations that can be moved out of loops to optimize performance.

The analysis has the following steps:
1. Identify leader statements
2. Form basic blocks
3. Build Control Flow Graph (CFG)
4. Compute dominators
5. Identify back edges (loops)
6. Identify natural loops
7. Perform data flow analysis
8. Find loop-invariant code
9. Determine which invariants can be safely moved

Use the Previous/Next buttons to step through the analysis.
Click on blocks in the CFG to see detailed information.
"""
        elif self.current_step == 1:  # Leader Statements
            info = """Leader Statements
            
Leader statements are the first statements of basic blocks. They include:
- The first statement of the program
- The target of any GOTO statement
- Any statement that follows a GOTO or conditional statement

Leader statements found:
"""
            for leader in self.analyzer.leaders:
                if leader <= len(self.input_tac):
                    info += f"  {leader}: {self.input_tac[leader-1]}\n"
        
        elif self.current_step == 2:  # Basic Blocks
            info = """Basic Blocks
            
A basic block is a sequence of consecutive statements with:
- A single entry point (the leader)
- A single exit point (the last statement)
- No branches except at the entry and exit

Basic blocks formed:
"""
            for block, stmts in self.analyzer.blocks.items():
                info += f"\n{block}:\n"
                for stmt in stmts:
                    if stmt <= len(self.input_tac):
                        info += f"  {stmt}: {self.input_tac[stmt-1]}\n"
        
        elif self.current_step == 3:  # Control Flow Graph
            info = """Control Flow Graph (CFG)
            
The CFG shows how control flows between basic blocks:
- Nodes represent basic blocks
- Edges represent possible execution paths
- Arrows indicate the direction of control flow

Block relationships:
"""
            for block in sorted(self.analyzer.blocks.keys()):
                info += f"\n{block}:\n"
                info += f"  Successors: {', '.join(self.analyzer.successors.get(block, []))}\n"
                info += f"  Predecessors: {', '.join(self.analyzer.predecessors.get(block, []))}\n"
        
        elif self.current_step == 4:  # Dominators
            info = """Dominators
            
A block X dominates block Y if every path from the entry block to Y must go through X.
In other words, X must be executed before Y in any execution of the program.

Dominator relationships:
"""
            for block in sorted(self.analyzer.blocks.keys()):
                info += f"\n{block} is dominated by: {', '.join(sorted(self.analyzer.dominators.get(block, [])))}\n"
        
        elif self.current_step == 5:  # Back Edges
            info = """Back Edges
            
A back edge is an edge from a node to one of its dominators.
Back edges indicate the presence of loops in the code.

Back edges found:
"""
            if self.analyzer.back_edges:
                for from_block, to_block in self.analyzer.back_edges:
                    info += f"  {from_block} -> {to_block}\n"
            else:
                info += "  No back edges found (code has no loops)\n"
        
        elif self.current_step == 6:  # Natural Loops
            info = """Natural Loops
            
A natural loop is formed by a back edge (A,B) where:
- B dominates A (B is the loop header)
- The loop body consists of all nodes that can reach A without going through B

Natural loops found:
"""
            if self.analyzer.loops:
                loop_num = 1
                for (header, tail), blocks in self.analyzer.loops.items():
                    info += f"\nLoop {loop_num} (Header: {header}, Back edge: {tail} -> {header}):\n"
                    info += f"  Blocks: {', '.join(blocks)}\n"
                    
                    # List all statements in the loop
                    info += "  Statements in loop:\n"
                    loop_stmts = []
                    for block in blocks:
                        loop_stmts.extend(self.analyzer.blocks.get(block, []))
                    
                    for stmt in sorted(loop_stmts):
                        if stmt <= len(self.input_tac):
                            info += f"    {stmt}: {self.input_tac[stmt-1]}\n"
                    
                    loop_num += 1
            else:
                info += "  No loops found in the code\n"
        
        elif self.current_step == 7:  # Data Flow Analysis
            info = """Data Flow Analysis
            
Data flow analysis calculates how variable definitions propagate through the program:

GEN set: Statements that define variables in a block
KILL set: Statements that are killed (redefined) by a block
IN set: Definitions that reach the beginning of a block
OUT set: Definitions that are live at the end of a block

See the 'Data Flow Tables' tab for visualizations of these sets.
"""
        
        elif self.current_step == 8:  # Loop-Invariant Code
            info = """Loop-Invariant Computations
            
Loop-invariant computations are statements whose results don't change within the loop.
A computation is invariant if:
- It doesn't use variables defined in the loop, or
- It only uses variables defined by other invariant computations

Loop-invariant computations found:
"""
            if self.analyzer.loop_invariants:
                for stmt in sorted(self.analyzer.loop_invariants):
                    if stmt <= len(self.input_tac):
                        info += f"  {stmt}: {self.input_tac[stmt-1]}\n"
            else:
                info += "  No loop-invariant computations found\n"
        
        elif self.current_step == 9:  # Code Motion
            info = """Loop-Invariant Code Motion
            
Not all loop-invariant computations can be safely moved out of the loop.
A computation is movable if:
1. It dominates all loop exits
2. There are no other definitions of the same variable in the loop
3. All uses in the loop are reached only by this definition

Movable loop-invariant computations:
"""
            if self.analyzer.movable_instructions:
                for stmt in sorted(self.analyzer.movable_instructions):
                    if stmt <= len(self.input_tac):
                        info += f"  {stmt}: {self.input_tac[stmt-1]}\n"
                        
                # Show the optimized code
                info += "\nOptimized Code (after moving invariant computations):\n"
                
                # Get loop headers and pre-headers
                loop_headers = [header for header, _ in self.analyzer.loops.keys()]
                pre_headers = {}
                for header in loop_headers:
                    pre_headers[header] = [pred for pred in self.analyzer.predecessors.get(header, []) 
                                         if pred not in self.analyzer.loops.get((header, None), [])]
                
                if pre_headers:
                    # Show what would be moved
                    for header, preds in pre_headers.items():
                        if preds:
                            pre_header = preds[0]
                            info += f"\nMoving to block {pre_header} (before loop header {header}):\n"
                            for stmt in self.analyzer.movable_instructions:
                                if stmt <= len(self.input_tac):
                                    info += f"  {self.input_tac[stmt-1]}\n"
            else:
                info += "  No movable loop-invariant computations found\n"
        
        self.info_scroll.insert(tk.END, info)
        self.info_scroll.config(state=tk.DISABLED)
    
    def update_explanation(self):
        """Update the explanation text based on the current step."""
        self.explanation_text.config(state=tk.NORMAL)
        self.explanation_text.delete(1.0, tk.END)
        
        explanations = [
            # 0: Introduction
            """Welcome to the Three Address Code Analyzer! This tool helps visualize the process of finding and removing loop invariant computations from code.

Three-address code (TAC) is an intermediate representation used in compilers where each instruction has at most three operands and typically performs a single operation.

Click 'Next' to begin analyzing the code step by step.""",
            
            # 1: Leader Statements
            """Leader statements are the first statements of basic blocks. They include:
- The first statement of the program
- Targets of GOTO statements
- Statements following conditional or unconditional jumps

Leader statements are highlighted in yellow in the code display.""",
            
            # 2: Basic Blocks
            """A basic block is a sequence of consecutive statements that:
- Has one entry point (at the beginning)
- Has one exit point (at the end)
- Has no branches except at the entry and exit

The code is now colored by blocks. Each block represents a straight-line sequence of code with no branches.""",
            
            # 3: Control Flow Graph
            """The Control Flow Graph (CFG) shows how control flows between basic blocks:
- Each node represents a basic block
- Each edge represents a possible control transfer

Click on any block in the graph to see detailed information about it. The CFG helps us understand the program's structure and identify loops.""",
            
            # 4: Dominators
            """A block X dominates block Y if every path from the entry block to Y must go through X.

Dominators are important for identifying loops and determining which code can be safely moved out of loops.

Click on a block in the CFG to see which blocks dominate it.""",
            
            # 5: Back Edges
            """A back edge is an edge from a node to one of its dominators. Back edges indicate the presence of loops in the code.

Back edges are highlighted in red in the CFG.

These edges are critical for identifying loop structures in the code.""",
            
            # 6: Natural Loops
            """A natural loop consists of:
- A header block (target of a back edge)
- All blocks that can reach the source of the back edge without going through the header

Natural loops are highlighted in the CFG. 

These are the code regions where we'll look for loop-invariant computations.""",
            
            # 7: Data Flow Analysis
            """Data flow analysis tracks how variable definitions propagate through the program:

- GEN: Statements that define variables
- KILL: Statements whose definitions are overwritten
- IN: Definitions reaching the beginning of a block
- OUT: Definitions leaving a block

See the 'Data Flow Tables' tab for detailed information.""",
            
            # 8: Loop-Invariant Code
            """Loop-invariant computations are statements whose results don't change within a loop.

A computation is invariant if it uses only values defined outside the loop or by other invariant computations.

Loop-invariant computations are highlighted in yellow.""",
            
            # 9: Code Motion
            """Loop-Invariant Code Motion is an optimization that moves invariant computations out of loops.

A computation can be moved if:
1. It dominates all loop exits
2. There are no other definitions of the same variable in the loop
3. All uses in the loop are reached only by this definition

Movable computations are highlighted in yellow."""
        ]
        
        self.explanation_text.insert(tk.END, explanations[self.current_step])
        self.explanation_text.config(state=tk.DISABLED)
    
    def update_display(self):
        """Update the entire display based on the current step."""
        # Update step label
        self.step_var.set(f"Step {self.current_step + 1} of {len(self.steps)}: {self.steps[self.current_step]}")
        
        # Enable/disable navigation buttons
        self.prev_button.config(state=tk.NORMAL if self.current_step > 0 else tk.DISABLED)
        self.next_button.config(state=tk.NORMAL if self.current_step < len(self.steps) - 1 else tk.DISABLED)
        
        # Update explanation
        self.update_explanation()
        
        # Update info display
        self.update_info_display()
        
        # Step-specific updates
        if self.current_step == 0:  # Introduction
            self.update_code_display()
            self.draw_cfg(show_cfg=False)
            self.draw_tables()
            self.tab_control.select(self.graph_tab)
            
        elif self.current_step == 1:  # Leader Statements
            self.highlighted_stmts = self.analyzer.leaders
            self.update_code_display(highlight_stmts=self.highlighted_stmts)
            self.draw_cfg(show_cfg=False)
            self.draw_tables()
            self.tab_control.select(self.graph_tab)
            
        elif self.current_step == 2:  # Basic Blocks
            self.update_code_display(color_blocks=True)
            self.draw_cfg(show_cfg=False)
            self.draw_tables()
            self.tab_control.select(self.graph_tab)
            
        elif self.current_step == 3:  # Control Flow Graph
            self.update_code_display(color_blocks=True)
            self.draw_cfg(show_cfg=True)
            self.draw_tables()
            self.tab_control.select(self.graph_tab)
            
        elif self.current_step == 4:  # Dominators
            self.update_code_display(color_blocks=True)
            self.draw_cfg(show_cfg=True)
            self.draw_tables()
            self.tab_control.select(self.graph_tab)
            
        elif self.current_step == 5:  # Back Edges
            self.update_code_display(color_blocks=True)
            self.draw_cfg(show_cfg=True, highlight_edges=self.analyzer.back_edges)
            self.draw_tables()
            self.tab_control.select(self.graph_tab)
            
        elif self.current_step == 6:  # Natural Loops
            loop_blocks = []
            for loop in self.analyzer.loops.values():
                loop_blocks.extend(loop)
            self.highlighted_blocks = loop_blocks
            
            self.update_code_display(color_blocks=True)
            self.draw_cfg(show_cfg=True, highlight_blocks=self.highlighted_blocks, 
                         highlight_edges=self.analyzer.back_edges)
            self.draw_tables()
            self.tab_control.select(self.graph_tab)
            
        elif self.current_step == 7:  # Data Flow Analysis
            self.update_code_display(color_blocks=True)
            self.draw_cfg(show_cfg=True)
            self.draw_tables()
            self.draw_ud_chains()  # Draw UD chains
            self.tab_control.select(self.table_tab)  # Switch to tables tab
            
        elif self.current_step == 8:  # Loop-Invariant Code
            self.highlighted_stmts = self.analyzer.loop_invariants
            self.update_code_display(highlight_stmts=self.highlighted_stmts, color_blocks=True)
            
            loop_blocks = []
            for loop in self.analyzer.loops.values():
                loop_blocks.extend(loop)
            self.highlighted_blocks = loop_blocks
            
            self.draw_cfg(show_cfg=True, highlight_blocks=self.highlighted_blocks,
                         highlight_edges=self.analyzer.back_edges)
            self.draw_tables()
            self.tab_control.select(self.graph_tab)
            
        elif self.current_step == 9:  # Code Motion
            self.highlighted_stmts = self.analyzer.movable_instructions
            self.update_code_display(highlight_stmts=self.highlighted_stmts, color_blocks=True)
            
            loop_blocks = []
            for loop in self.analyzer.loops.values():
                loop_blocks.extend(loop)
            self.highlighted_blocks = loop_blocks
            
            self.draw_cfg(show_cfg=True, highlight_blocks=self.highlighted_blocks,
                         highlight_edges=self.analyzer.back_edges)
            self.draw_tables()
            self.tab_control.select(self.info_tab)  # Show detailed optimization info
        
        # Update block details if a block is selected
        if self.selected_block:
            self.update_block_details(self.selected_block)
        
        # Update UD chains display if in step 7+
        if self.current_step >= 7:
            self.draw_ud_chains()
    
    def next_step(self):
        """Advance to the next step in the analysis."""
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            
            # Run analysis for the current step if needed
            self._ensure_analysis_up_to_step(self.current_step)
            
            self.update_display()
            
            # Cancel any auto-playing
            if self.auto_playing:
                self.toggle_auto_play()
    
    def previous_step(self):
        """Go back to the previous step."""
        if self.current_step > 0:
            self.current_step -= 1
            self.update_display()
            
            # Cancel any auto-playing
            if self.auto_playing:
                self.toggle_auto_play()
    
    def toggle_auto_play(self):
        """Toggle automatic advancement through steps."""
        if self.auto_playing:
            # Stop auto-play
            self.auto_playing = False
            self.auto_button.config(text="Auto Play")
            if hasattr(self, 'auto_id'):
                self.root.after_cancel(self.auto_id)
        else:
            # Start auto-play
            self.auto_playing = True
            self.auto_button.config(text="Stop")
            self._auto_advance()
    
    def _auto_advance(self):
        """Automatically advance to the next step after a delay."""
        if self.current_step < len(self.steps) - 1:
            self.next_step()
            self.auto_id = self.root.after(self.auto_delay, self._auto_advance)
        else:
            self.toggle_auto_play()  # Stop when we reach the end
    
    def _ensure_analysis_up_to_step(self, step):
        """Ensure the analysis has been run up to the specified step."""
        if step >= 1 and not self.analyzer.leaders:
            self.analyzer.identify_leaders()
        
        if step >= 2 and not self.analyzer.blocks:
            self.analyzer.form_basic_blocks()
        
        if step >= 3 and not self.analyzer.successors:
            self.analyzer.build_cfg()
        
        if step >= 4 and not self.analyzer.dominators:
            self.analyzer.compute_dominators()
        
        if step >= 5 and not self.analyzer.back_edges:
            self.analyzer.identify_back_edges()
        
        if step >= 6 and not self.analyzer.loops:
            self.analyzer.identify_loops()
        
        if step >= 7 and not self.analyzer.gen:
            self.analyzer.compute_gen_kill()
            self.analyzer.compute_in_out()
            self.analyzer.compute_ud_chains()  # Compute UD-chains after data flow analysis
        
        if step >= 8 and not self.analyzer.loop_invariants:
            self.analyzer.identify_loop_invariants()
        
        if step >= 9 and not self.analyzer.movable_instructions:
            self.analyzer.identify_movable_invariants()
    
    def on_closing(self):
        """Handle closing the window."""
        plt.close('all')  # Close all matplotlib figures
        self.root.destroy()


if __name__ == "__main__":
    # For direct testing
    root = tk.Tk()
    app = TACVisualization(root)
    root.mainloop()