import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import scipy.io
import pandas as pd
import numpy as np

class MatViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MATLAB Full Data Explorer")
        self.root.geometry("1000x800")

        # --- UI Layout ---
        self.top_frame = tk.Frame(root)
        self.top_frame.pack(pady=10, fill='x')

        self.open_btn = tk.Button(self.top_frame, text="📁 Open .mat File", command=self.load_file, bg="#2b78e4", fg="white", padx=10)
        self.open_btn.pack(side=tk.LEFT, padx=10)

        tk.Label(self.top_frame, text="Variable:").pack(side=tk.LEFT, padx=5)
        self.var_selector = ttk.Combobox(self.top_frame, state="readonly", width=30)
        self.var_selector.pack(side=tk.LEFT, padx=5)
        self.var_selector.bind("<<ComboboxSelected>>", self.on_variable_selected)

        # Main Data Table
        self.table_frame = tk.Frame(root)
        self.table_frame.pack(expand=True, fill='both', padx=10)

        self.tree = ttk.Treeview(self.table_frame)
        self.tree.pack(expand=True, fill='both', side=tk.LEFT)
        self.tree.bind("<<TreeviewSelect>>", self.on_row_select) # Update detail view on click
        self.tree.bind("<Button-3>", self.show_context_menu)     # Right-click to copy

        self.scrolly = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        self.scrolly.pack(side=tk.RIGHT, fill='y')
        self.tree.configure(yscrollcommand=self.scrolly.set)

        # --- NEW: Detail View (Bottom Text Box) ---
        tk.Label(root, text="Cell Detail (Full Content):", anchor="w").pack(fill="x", padx=10)
        self.detail_text = tk.Text(root, height=8, padx=10, pady=10, wrap="word", bg="#f4f4f4")
        self.detail_text.pack(fill="x", padx=10, pady=(0, 10))

        # --- NEW: Right-Click Menu ---
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Copy Cell Content", command=self.copy_to_clipboard)

        self.mat_contents = {}

    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("MATLAB files", "*.mat")])
        if file_path:
            try:
                raw_data = scipy.io.loadmat(file_path)
                self.mat_contents = {k: v for k, v in raw_data.items() if not k.startswith('__')}
                if self.mat_contents:
                    self.var_selector['values'] = list(self.mat_contents.keys())
                    self.var_selector.current(0)
                    self.on_variable_selected(None)
            except Exception as e:
                messagebox.showerror("Error", f"Could not read file: {e}")

    def on_variable_selected(self, event):
        var_name = self.var_selector.get()
        data = self.mat_contents[var_name]
        try:
            if data.dtype.names is not None:
                structured_dict = {name: data[name].flatten() for name in data.dtype.names}
                for key in structured_dict:
                    if len(structured_dict[key]) > 0 and isinstance(structured_dict[key][0], np.ndarray):
                        structured_dict[key] = [x.item() if x.size==1 else x for x in structured_dict[key]]
                df = pd.DataFrame(structured_dict)
            else:
                df = pd.DataFrame(data)
            self.display_data(df)
        except Exception as e:
            messagebox.showerror("Display Error", str(e))

    def display_data(self, df):
        self.tree.delete(*self.tree.get_children())
        cols = [str(c) for c in df.columns]
        self.tree["columns"] = cols
        self.tree["show"] = "headings"
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        for _, row in df.head(1000).iterrows():
            clean_row = [self.clean_val(v) for v in row]
            self.tree.insert("", "end", values=clean_row)

    def clean_val(self, val):
        """A 'Healthier' cleaner: Summarizes data instead of expanding it."""
        if isinstance(val, np.ndarray):
            if val.size == 0:
                return ""
            if val.size == 1:
                return val.item()
            # If it's a large array, don't convert to string yet! 
            # Just show a summary to prevent the UI from crashing.
            return f"Array {val.shape} (Click to view)"
        
        # Limit text length in the main table to 50 characters
        str_val = str(val)
        return (str_val[:50] + '...') if len(str_val) > 50 else str_val

    def on_variable_selected(self, event):
        var_name = self.var_selector.get()
        data = self.mat_contents[var_name]
        try:
            if data.dtype.names is not None:
                structured_dict = {name: data[name].flatten() for name in data.dtype.names}
                for key in structured_dict:
                    if len(structured_dict[key]) > 0 and isinstance(structured_dict[key][0], np.ndarray):
                        structured_dict[key] = [x.item() if x.size==1 else x for x in structured_dict[key]]
                df = pd.DataFrame(structured_dict)
            else:
                df = pd.DataFrame(data)

            # --- THE FIX IS HERE ---
            self.current_df = df  # This saves it so on_row_select can see it
            # -----------------------

            self.display_data(df)
        except Exception as e:
            messagebox.showerror("Display Error", str(e))

    def on_row_select(self, event):
        """Safely unpacks data from self.current_df."""
        selected_item = self.tree.selection()
        if not selected_item:
            return

        # Check if current_df exists before using it
        if not hasattr(self, 'current_df'):
            return

        idx = self.tree.index(selected_item[0])
        
        # Pull the row from the 'backpack'
        row = self.current_df.iloc[idx]

        self.detail_text.config(state="normal")
        self.detail_text.delete("1.0", tk.END)
        
        details = []
        for col_name, value in row.items():
            # Only expand to string now, on demand
            if isinstance(value, np.ndarray):
                full_val = str(value.tolist())
            else:
                full_val = str(value)
            details.append(f"== {col_name} ==\n{full_val}\n")
        
        self.detail_text.insert("1.0", "\n".join(details))
        self.detail_text.config(state="disabled")
    def show_context_menu(self, event):
        """Show right-click menu at the mouse position."""
        iid = self.tree.identify_row(event.y)
        if iid:
            self.tree.selection_set(iid)
            self.context_menu.post(event.x_root, event.y_root)

    def copy_to_clipboard(self):
        """Copy the detail text content to the Windows/System clipboard."""
        content = self.detail_text.get("1.0", tk.END).strip()
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        messagebox.showinfo("Copied", "Content copied to clipboard!")

if __name__ == "__main__":
    root = tk.Tk()
    app = MatViewerApp(root)
    root.mainloop()