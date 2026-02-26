import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import scipy.io
import pandas as pd
import numpy as np  # Added this for data checking

class MatViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MATLAB File Explorer")
        self.root.geometry("800x600")

        # --- UI Layout ---
        self.top_frame = tk.Frame(root)
        self.top_frame.pack(pady=10)

        self.open_btn = tk.Button(self.top_frame, text="Open .mat File", command=self.load_file, bg="#2b78e4", fg="white", padx=10)
        self.open_btn.pack(side=tk.LEFT, padx=5)

        self.label = tk.Label(self.top_frame, text="No file selected", fg="grey")
        self.label.pack(side=tk.LEFT, padx=5)

        self.table_frame = tk.Frame(root)
        self.table_frame.pack(expand=True, fill='both', padx=10, pady=10)

        self.tree = ttk.Treeview(self.table_frame)
        self.tree.pack(expand=True, fill='both', side=tk.LEFT)

        self.scrolly = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        self.scrolly.pack(side=tk.RIGHT, fill='y')
        self.tree.configure(yscrollcommand=self.scrolly.set)

    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("MATLAB files", "*.mat")])
        
        if file_path:
            self.label.config(text=file_path.split("/")[-1])
            try:
                mat_data = scipy.io.loadmat(file_path)
                data_keys = [k for k in mat_data.keys() if not k.startswith('__')]
                
                if not data_keys:
                    messagebox.showwarning("Empty File", "No data found.")
                    return

                main_key = data_keys[0]
                data = mat_data[main_key]

                # --- NEW LOGIC: Flattening the MATLAB Table Structure ---
                if data.dtype.names is not None:
                    # The data is "structured". We need to extract each field
                    # to avoid the "25 columns vs 1 column" error.
                    structured_dict = {name: data[name].flatten() for name in data.dtype.names}
                    
                    # We need to make sure all columns have the same length
                    # (MATLAB sometimes adds extra nesting)
                    for key in structured_dict:
                        if len(structured_dict[key]) > 0 and isinstance(structured_dict[key][0], np.ndarray):
                           structured_dict[key] = [x.item() if x.size==1 else x for x in structured_dict[key]]

                    df = pd.DataFrame(structured_dict)
                else:
                    df = pd.DataFrame(data)               

                self.display_data(df)

            except Exception as e:
                import traceback
                print(traceback.format_exc()) # This prints the full error to your VS 2022 console
                messagebox.showerror("Error", f"Could not read file: {e}")

    def display_data(self, df):
        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 1. Clean up Column Names
        cols = [str(c) for c in df.columns]
        self.tree["columns"] = cols
        self.tree["show"] = "headings"

        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")

        # 2. Clean up Row Data
        for _, row in df.head(500).iterrows():
            clean_row = []
            for val in row:
                # --- FIX: Deep cleaning of NumPy objects ---
                if isinstance(val, np.ndarray):
                    if val.size == 1:
                        clean_row.append(val.item())
                    else:
                        clean_row.append(str(val.tolist())) # lowercase .tolist()
                else:
                    clean_row.append(val)
            
            self.tree.insert("", "end", values=clean_row)

if __name__ == "__main__":
    root = tk.Tk()
    app = MatViewerApp(root)
    root.mainloop()