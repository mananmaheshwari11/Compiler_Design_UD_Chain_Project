#!/usr/bin/env python3
# new_run_visualization.py - Runner for TAC Visualization with UD-Chains

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import re
import os
import sys
import traceback
from new_tac_visualization import TACVisualization

class TACStartupApp:
    """A startup screen for the Three Address Code Analyzer."""
    def __init__(self, root):
        self.root = root
        self.root.title("Three Address Code Analyzer - Startup")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # Main frame
        main_frame = ttk.Frame(root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="Three Address Code Analysis & Visualization",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Description
        desc_text = (
            "This tool visualizes the process of analyzing Three Address Code (TAC) "
            "to identify loop-invariant computations that can be safely moved out of loops. "
            "The visualization shows each step of the analysis in detail."
        )
        desc_label = ttk.Label(
            main_frame,
            text=desc_text,
            wraplength=600,
            justify=tk.CENTER
        )
        desc_label.pack(pady=(0, 20))
        
        # Code section
        code_frame = ttk.LabelFrame(main_frame, text="Three Address Code")
        code_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Example selection
        example_frame = ttk.Frame(code_frame)
        example_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(example_frame, text="Select Example:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.example_var = tk.StringVar(value="array_sum")
        example_combo = ttk.Combobox(
            example_frame, 
            textvariable=self.example_var,
            values=["array_sum", "loop_with_invariant", "nested_loops", "custom"],
            width=20,
            state="readonly"
        )
        example_combo.pack(side=tk.LEFT)
        example_combo.bind("<<ComboboxSelected>>", self.update_example_code)
        
        # Code editor
        self.code_text = scrolledtext.ScrolledText(
            code_frame, 
            wrap=tk.NONE, 
            width=60, 
            height=15,
            font=("Courier", 10)
        )
        self.code_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Load from file button
        load_button = ttk.Button(
            button_frame, 
            text="Load from File", 
            command=self.load_from_file,
            width=15
        )
        load_button.pack(side=tk.LEFT, padx=5)
        
        # Spacer
        ttk.Frame(button_frame).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Start button
        start_button = ttk.Button(
            button_frame, 
            text="Start Analysis", 
            command=self.start_analysis,
            width=15
        )
        start_button.pack(side=tk.RIGHT, padx=5)
        
        # Example code templates
        self.examples = {
            "array_sum": [
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
            ],
            "loop_with_invariant": [
                "count = 0",
                "result = 0",
                "If count > 20 GOTO 8",
                "count = count + 1",
                "increment = 2 * count",
                "result = result + increment",
                "GOTO 3",
                "return result"
            ],
            "nested_loops": [
                "i = 1",
                "sum = 0",
                "If i > n GOTO 15",
                "j = 1",
                "If j > m GOTO 13",
                "t1 = i * m",
                "t2 = t1 + j",
                "t3 = t2 - 1",
                "t4 = a[t3]",
                "sum = sum + t4",
                "j = j + 1",
                "GOTO 5",
                "i = i + 1",
                "GOTO 3",
                "return sum"
            ],
            "double_loop": [
                "a = 0"
                "b = 1"
                "c = 2"
                "If (b>100) GOTO 15"
                "a = a + 1"
                "d = e + f"
                "If (b>50) GOTO 13"
                "c = a"
                "g = 10 * d"
                "h = g + c"
                "b = b + 2"
                "GOTO 7"
                "b = b + 4"
                "GOTO 4"
                "i = b"
            ],
            "custom": []  # Custom code will be kept as is
        }
        
        # Initialize with default example
        self.update_example_code()
    
    def update_example_code(self, event=None):
        """Update the code editor with the selected example"""
        example_key = self.example_var.get()
        
        # Only update if not custom
        if example_key != "custom":
            self.code_text.delete(1.0, tk.END)
            code = "\n".join(self.examples[example_key])
            self.code_text.insert(tk.END, code)
    
    def load_from_file(self):
        """Load code from a file"""
        file_path = filedialog.askopenfilename(
            title="Select Three Address Code File",
            filetypes=[("Text Files", "*.txt"), ("Python Files", "*.py"), ("All Files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r') as file:
                content = file.read()
                
                # Try to extract TAC array from Python code if it's there
                tac_match = re.search(r'input_tac\s*=\s*\[(.*?)\]', content, re.DOTALL)
                
                if tac_match:
                    # Extract the array contents
                    array_content = tac_match.group(1)
                    
                    # Parse the array elements
                    lines = []
                    for line in re.finditer(r'"([^"]*)"', array_content):
                        lines.append(line.group(1))
                    
                    if not lines:
                        # Try with single quotes
                        for line in re.finditer(r"'([^']*)'", array_content):
                            lines.append(line.group(1))
                    
                    if lines:
                        self.code_text.delete(1.0, tk.END)
                        self.code_text.insert(tk.END, "\n".join(lines))
                        self.example_var.set("custom")
                        return
                
                # If not found as an array, treat the whole file as TAC
                self.code_text.delete(1.0, tk.END)
                self.code_text.insert(tk.END, content)
                self.example_var.set("custom")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {str(e)}")
    
    def start_analysis(self):
        """Start the visualization with the current code"""
        # Get the code from the text editor
        code_text = self.code_text.get(1.0, tk.END).strip()
        
        if not code_text:
            messagebox.showerror("Error", "Please enter or select some code first.")
            return
        
        # Parse the code into lines
        lines = code_text.split("\n")
        
        # Close the startup window
        self.root.withdraw()
        
        try:
            # Create new window for visualization
            viz_root = tk.Toplevel(self.root)
            viz_root.protocol("WM_DELETE_WINDOW", self.on_viz_closing)
            
            # Start the visualization
            self.visualization = TACVisualization(viz_root, lines)
            
        except Exception as e:
            self.root.deiconify()  # Show startup screen again
            messagebox.showerror("Error", f"Error starting visualization: {str(e)}\n\n{traceback.format_exc()}")
    
    def on_viz_closing(self):
        """Handle closing the visualization window"""
        # Close the visualization
        if hasattr(self, 'visualization'):
            try:
                self.visualization.on_closing()
            except:
                pass
        
        # Show the startup screen again
        self.root.deiconify()


def main():
    root = tk.Tk()
    app = TACStartupApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()