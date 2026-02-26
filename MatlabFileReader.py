import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import scipy.io
import pandas as pd
import numpy as np

class MatViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MATLAB Full Data Explorer")
        self.root.geometry("1000x700")

        # --- UI Layout ---
        self.top_frame = tk.Frame(root)
        self.top_frame.pack(pady=10, fill='x')

        # 1. Open Button
        self.open_btn = tk.Button(self.top_frame, text="📁 Open .mat File", command=self.load_file, bg="#2b78e4", fg="white", padx=10)
        self.open_btn.pack(side=tk.LEFT, padx=10)

        # 2. Variable Selector Dropdown
        tk.Label(self.top_frame, text="Select Variable:").pack(side=tk.LEFT, padx=5)
        self.var_selector = ttk.Combobox(self.top_frame, state="readonly", width=30)
        self.var_selector.pack(side=tk.LEFT, padx=5)
        self.var_selector.bind("<<ComboboxSelected>>", self.on_variable_selected)

        self.label = tk.Label(self.top_frame, text="No file loaded", fg="grey")
        self.label.pack(side=tk.LEFT, padx=10)

        # 3. Table Area
        self.table_frame = tk.Frame(root)
        self.table_frame.pack(expand=True, fill='both', padx=10, pady=10)

        self.tree = ttk.Treeview(self.table_frame)
        self.tree.pack(expand=True, fill='both', side=tk.LEFT)

        self.scrolly = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        self.scrolly.pack(side=tk.RIGHT, fill='y')
        self.scrollx = ttk.Scrollbar(root, orient="horizontal", command=self.tree.xview) # Added horizontal scroll
        self.scrollx.pack(fill='x')
        
        self.tree.configure(yscrollcommand=self.scrolly.set, xscrollcommand=self.scrollx.set)

        self.mat_contents = {} # Local storage for file data

    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("MATLAB files", "*.mat")])
        if not file_path:
            return

        try:
            # Load the whole file once
            raw_data = scipy.io.loadmat(file_path)
            # Filter out metadata
            self.mat_contents = {k: v for k, v in raw_data.items() if not k.startswith('__')}
            
            if not self.mat_contents:
                messagebox.showwarning("Empty", "No data found in file.")
                return

            # Update Dropdown
            self.var_selector['values'] = list(self.mat_contents.keys())
            self.var_selector.current(0) # Select the first one by default
            self.on_variable_selected(None)
            
            self.label.config(text=f"Loaded: {file_path.split('/')[-1]}", fg="black")

        except Exception as e:
            messagebox.showerror("Error", f"Could not read file: {e}")

    def on_variable_selected(self, event):
        var_name = self.var_selector.get()
        data = self.mat_contents[var_name]
        
        try:
            # Handle Structured Arrays (Tables) vs Normal Matrices
            if data.dtype.names is not None:
                structured_dict = {name: data[name].flatten() for name in data.dtype.names}
                for key in structured_dict:
                    # Deep cleaning
                    if len(structured_dict[key]) > 0 and isinstance(structured_dict[key][0], np.ndarray):
                        structured_dict[key] = [x.item() if x.size==1 else x for x in structured_dict[key]]
                df = pd.DataFrame(structured_dict)
            else:
                df = pd.DataFrame(data)

            self.display_data(df)
        except Exception as e:
            messagebox.showerror("Display Error", f"Variable {var_name} is complex: {e}")

    def display_data(self, df):
        self.tree.delete(*self.tree.get_children())
        
        cols = [str(c) for c in df.columns]
        self.tree["columns"] = cols
        self.tree["show"] = "headings"

        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, minwidth=50, stretch=True)

        # Show top 1000 rows (adjust for speed)
        for _, row in df.head(1000).iterrows():
            clean_row = []
            for val in row:
                if isinstance(val, np.ndarray):
                    clean_row.append(val.item() if val.size == 1 else str(val.tolist()))
                else:
                    clean_row.append(val)
            self.tree.insert("", "end", values=clean_row)

if __name__ == "__main__":
    root = tk.Tk()
    app = MatViewerApp(root)
    root.mainloop()