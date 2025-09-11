import tkinter as tk
from tkinter import ttk, messagebox
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time

# ---------------- Backend ---------------- #
def solve_max_flow(edges, source, sink):
    G = nx.DiGraph()
    for u, v, capacity in edges:
        G.add_edge(u, v, capacity=capacity)
    flow_value, flow_dict = nx.maximum_flow(G, source, sink)
    return flow_value, flow_dict, G

# ---------------- Frontend ---------------- #
class NetworkFlowApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Network Flow Visualizer")
        self.root.geometry("1250x950")  # larger window
        self.edges = []

        # ----- Color Palette ----- #
        self.bg_color = "#e6f2ff"
        self.frame_color = "#cce0ff"
        self.input_color = "#ffffff"
        self.listbox_color = "#f2f7ff"
        self.accent_color = "#3399ff"
        self.root.configure(bg=self.bg_color)

        # ----- Styling ----- #
        style = ttk.Style()
        style.theme_use('clam')

        style.configure("TLabel", font=('Segoe UI', 12), background=self.frame_color)
        style.configure("TButton", font=('Segoe UI', 12, 'bold'),
                        padding=8, relief="flat", background=self.accent_color, foreground="white")
        style.map("TButton", background=[("active", "#2675cc")])

        style.configure("Header.TLabel", font=('Segoe UI', 22, 'bold'),
                        background=self.bg_color, foreground="#004080")
        style.configure("Section.TLabel", font=('Segoe UI', 16, 'bold'),
                        background=self.bg_color, foreground="#004080")

        style.configure("Rounded.TEntry", relief="flat", padding=6, font=("Segoe UI", 12))
        style.configure("TLabelframe", background=self.frame_color)
        style.configure("TLabelframe.Label", background=self.frame_color,
                        font=('Segoe UI', 14, 'bold'))

        # ----- Header ----- #
        ttk.Label(root, text="Network Flow Visualizer", style="Header.TLabel").pack(pady=20)

        # ----- Input Frame ----- #
        ttk.Label(root, text="Step 1: Add Connections Between Nodes", style="Section.TLabel").pack(pady=5)
        self.input_frame = ttk.LabelFrame(root, text="Connection Details")
        self.input_frame.pack(fill='x', padx=20, pady=10)

        ttk.Label(self.input_frame, text="From Node:").grid(row=0, column=0, padx=5, pady=5)
        self.from_entry = ttk.Entry(self.input_frame, width=12, style="Rounded.TEntry")
        self.from_entry.grid(row=0, column=1, padx=5)

        ttk.Label(self.input_frame, text="To Node:").grid(row=0, column=2, padx=5, pady=5)
        self.to_entry = ttk.Entry(self.input_frame, width=12, style="Rounded.TEntry")
        self.to_entry.grid(row=0, column=3, padx=5)

        ttk.Label(self.input_frame, text="Capacity (max flow allowed):").grid(row=0, column=4, padx=5, pady=5)
        self.capacity_entry = ttk.Entry(self.input_frame, width=12, style="Rounded.TEntry")
        self.capacity_entry.grid(row=0, column=5, padx=5)

        ttk.Button(self.input_frame, text="Add Connection", command=self.add_edge).grid(row=0, column=6, padx=10)
        ttk.Button(self.input_frame, text="Remove Selected", command=self.clear_selected_edge).grid(row=0, column=7, padx=10)
        ttk.Button(self.input_frame, text="Clear All", command=self.clear_all_edges).grid(row=0, column=8, padx=10)

        # Connection list #
        self.edge_listbox = tk.Listbox(root, width=95, height=6, bg=self.listbox_color,
                                       font=('Segoe UI', 12), relief="flat", bd=3, highlightthickness=0)
        self.edge_listbox.pack(pady=10)

        # ----- Source and Sink ----- #
        ttk.Label(root, text="Step 2: Define Start and End Nodes", style="Section.TLabel").pack(pady=5)
        source_sink_frame = ttk.Frame(root, style="TLabelframe")
        source_sink_frame.pack(pady=10)

        ttk.Label(source_sink_frame, text="Start (Source Node):").grid(row=0, column=0, padx=5, pady=5)
        self.source_entry = ttk.Entry(source_sink_frame, width=12, style="Rounded.TEntry")
        self.source_entry.grid(row=0, column=1, padx=5)

        ttk.Label(source_sink_frame, text="End (Sink Node):").grid(row=0, column=2, padx=5, pady=5)
        self.sink_entry = ttk.Entry(source_sink_frame, width=12, style="Rounded.TEntry")
        self.sink_entry.grid(row=0, column=3, padx=5)

        # ----- Solve button ----- #
        ttk.Button(root, text="🚀 Solve & Visualize Flow", command=self.start_solve_thread).pack(pady=20)

        # ----- Results Section ----- #
        ttk.Label(root, text="Step 3: Results", style="Section.TLabel").pack(pady=5)
        self.result_text = tk.Text(root, height=6, width=95, font=("Segoe UI", 11),
                                   bg=self.listbox_color, relief="flat", wrap="word")
        self.result_text.pack(pady=10)

        # ----- Graph Canvas (larger + taller) ----- #
        viz_frame = ttk.Frame(root)
        viz_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.figure = plt.Figure(figsize=(11,11))  # taller visualization area
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=viz_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    # ----- Add Edge ----- #
    def add_edge(self):
        u = self.from_entry.get()
        v = self.to_entry.get()
        cap = self.capacity_entry.get()

        if not u or not v or not cap:
            messagebox.showerror("Input Error", "All fields must be filled!")
            return

        try:
            cap = float(cap)
        except:
            messagebox.showerror("Input Error", "Capacity must be a number!")
            return

        self.edges.append((u, v, cap))
        self.edge_listbox.insert(tk.END, f"Connection: {u} → {v} | Capacity: {cap}")

        self.from_entry.delete(0, tk.END)
        self.to_entry.delete(0, tk.END)
        self.capacity_entry.delete(0, tk.END)

    # ----- Clear Selected ----- #
    def clear_selected_edge(self):
        selected = self.edge_listbox.curselection()
        if not selected:
            messagebox.showwarning("Selection Error", "No connection selected!")
            return
        index = selected[0]
        self.edge_listbox.delete(index)
        self.edges.pop(index)

    # ----- Clear All ----- #
    def clear_all_edges(self):
        if messagebox.askyesno("Clear All", "Are you sure you want to remove all connections?"):
            self.edge_listbox.delete(0, tk.END)
            self.edges.clear()

    # ----- Solve in Thread ----- #
    def start_solve_thread(self):
        thread = threading.Thread(target=self.solve_flow)
        thread.start()

    # ----- Solve Flow & Animate ----- #
    def solve_flow(self):
        source = self.source_entry.get()
        sink = self.sink_entry.get()

        if not source or not sink:
            messagebox.showerror("Input Error", "Start and End nodes must be specified!")
            return

        try:
            max_flow, flow_dict, G = solve_max_flow(self.edges, source, sink)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            return

        # ----- Update results ----- #
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, f"✅ The maximum possible flow from {source} to {sink} is {max_flow} units.\n\n")
        self.result_text.insert(tk.END, "Here’s how the flow is distributed through the connections:\n\n")
        for u, flows in flow_dict.items():
            for v, f in flows.items():
                if f > 0:
                    self.result_text.insert(tk.END, f"• {f} units go from {u} → {v}\n")

        # ----- Graph visualization ----- #
        self.ax.clear()
        pos = nx.spring_layout(G, seed=42)
        nx.draw_networkx_nodes(G, pos, ax=self.ax, node_color='skyblue', node_size=1000)
        nx.draw_networkx_labels(G, pos, ax=self.ax, font_size=12)

        nx.draw_networkx_edges(G, pos, ax=self.ax, edge_color="lightgray", arrows=True, arrowsize=20)
        self.canvas.draw()

        # ----- Animate edges ----- #
        def animate_edges():
            for u, v in G.edges():
                flow = flow_dict[u][v] if v in flow_dict[u] else 0
                capacity = G[u][v]['capacity']
                color_ratio = flow / capacity if capacity != 0 else 0
                nx.draw_networkx_edges(G, pos, edgelist=[(u,v)], ax=self.ax,
                                       edge_color=plt.cm.Blues(color_ratio),
                                       arrows=True, arrowsize=20, width=3)
                nx.draw_networkx_edge_labels(G, pos,
                                             edge_labels={(u,v): f"{flow}/{capacity}"},
                                             ax=self.ax, font_color='darkblue')
                self.canvas.draw()
                time.sleep(0.5)

        anim_thread = threading.Thread(target=animate_edges)
        anim_thread.start()


# ---------------- Run App ---------------- #
if __name__ == "__main__":
    root = tk.Tk()
    app = NetworkFlowApp(root)
    root.mainloop()
