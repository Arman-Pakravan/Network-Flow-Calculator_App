import tkinter as tk
from tkinter import ttk, messagebox
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading

# ---------------- Backend ---------------- #
def solve_max_flow(edges, source, sink):
    """
    edges: list of (u, v, capacity)
    Returns: (flow_value, flow_dict, G)
    """
    # aggregate duplicate edges (sum capacities)
    cap_map = {}
    for u, v, cap in edges:
        if cap < 0:
            raise ValueError("Capacities must be non-negative")
        cap_map[(u, v)] = cap_map.get((u, v), 0) + cap

    G = nx.DiGraph()
    for (u, v), capacity in cap_map.items():
        G.add_edge(u, v, capacity=capacity)

    # Explicitly use Edmonds–Karp
    flow_value, flow_dict = nx.maximum_flow(
        G, source, sink, flow_func=nx.algorithms.flow.edmonds_karp
    )
    return flow_value, flow_dict, G


# ---------------- Frontend ---------------- #
class NetworkFlowApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Network Flow Visualizer")
        self.root.geometry("1250x1000")
        self.edges = []

        # Configure grid
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)

        # ----- Colors & Styles ----- #
        self.bg_color = "#e6f2ff"
        self.frame_color = "#d0e4ff"
        self.listbox_color = "#f0f8ff"
        self.accent_color = "#3399ff"
        self.root.configure(bg=self.bg_color)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TLabel", font=('Segoe UI', 12), background=self.frame_color)
        style.configure("TButton", font=('Segoe UI', 12, 'bold'),
                        padding=8, relief="flat", background=self.accent_color, foreground="white")
        style.map("TButton", background=[("active", "#2675cc")])
        style.configure("Header.TLabel", font=('Segoe UI', 22, 'bold'),
                        background=self.bg_color, foreground="#003366")
        style.configure("Section.TLabel", font=('Segoe UI', 16, 'bold'),
                        background=self.bg_color, foreground="#003366")
        style.configure("Rounded.TEntry", relief="flat", padding=6, font=("Segoe UI", 12))
        style.configure("TLabelframe", background=self.frame_color)
        style.configure("TLabelframe.Label", background=self.frame_color,
                        font=('Segoe UI', 14, 'bold'))

        # ----- Controls ----- #
        controls = ttk.Frame(root, style="TLabelframe")
        controls.grid(row=0, column=0, sticky="ew")
        controls.columnconfigure(0, weight=1)

        ttk.Label(controls, text="Network Flow Visualizer", style="Header.TLabel").pack(pady=10)

        # Step 1
        ttk.Label(controls, text="Step 1: Add Connections Between Nodes", style="Section.TLabel").pack()
        self.input_frame = ttk.LabelFrame(controls, text="Connection Details")
        self.input_frame.pack(fill='x', padx=20, pady=10)

        ttk.Label(self.input_frame, text="From Node:").grid(row=0, column=0, padx=5, pady=5)
        self.from_entry = ttk.Entry(self.input_frame, width=12, style="Rounded.TEntry")
        self.from_entry.grid(row=0, column=1, padx=5)

        ttk.Label(self.input_frame, text="To Node:").grid(row=0, column=2, padx=5, pady=5)
        self.to_entry = ttk.Entry(self.input_frame, width=12, style="Rounded.TEntry")
        self.to_entry.grid(row=0, column=3, padx=5)

        ttk.Label(self.input_frame, text="Capacity:").grid(row=0, column=4, padx=5, pady=5)
        self.capacity_entry = ttk.Entry(self.input_frame, width=12, style="Rounded.TEntry")
        self.capacity_entry.grid(row=0, column=5, padx=5)

        ttk.Button(self.input_frame, text="Add", command=self.add_edge).grid(row=0, column=6, padx=10)
        ttk.Button(self.input_frame, text="Remove Selected", command=self.clear_selected_edge).grid(row=0, column=7, padx=10)
        ttk.Button(self.input_frame, text="Clear All", command=self.clear_all_edges).grid(row=0, column=8, padx=10)

        # Edge list
        self.edge_listbox = tk.Listbox(controls, width=95, height=5, bg=self.listbox_color,
                                       font=('Segoe UI', 12), relief="flat", bd=3)
        self.edge_listbox.pack(pady=10)

        # Step 2
        ttk.Label(controls, text="Step 2: Define Start and End Nodes", style="Section.TLabel").pack()
        source_sink_frame = ttk.Frame(controls, style="TLabelframe")
        source_sink_frame.pack(pady=10)

        ttk.Label(source_sink_frame, text="Start Node:").grid(row=0, column=0, padx=5, pady=5)
        self.source_entry = ttk.Entry(source_sink_frame, width=12, style="Rounded.TEntry")
        self.source_entry.grid(row=0, column=1, padx=5)

        ttk.Label(source_sink_frame, text="End Node:").grid(row=0, column=2, padx=5, pady=5)
        self.sink_entry = ttk.Entry(source_sink_frame, width=12, style="Rounded.TEntry")
        self.sink_entry.grid(row=0, column=3, padx=5)

        ttk.Button(controls, text="🚀 Solve & Visualize Flow", command=self.start_solve_thread).pack(pady=15)

        # Step 3
        ttk.Label(controls, text="Step 3: Results", style="Section.TLabel").pack()
        self.result_text = tk.Text(controls, height=5, width=95, font=("Segoe UI", 11),
                                   bg=self.listbox_color, relief="flat", wrap="word")
        self.result_text.pack(pady=10)

        # ----- Visualization Frame ----- #
        viz_frame = ttk.Frame(root, style="TLabelframe")
        viz_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)
        viz_frame.rowconfigure(0, weight=1)
        viz_frame.columnconfigure(0, weight=1)

        self.figure = plt.Figure(figsize=(13, 15))
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=viz_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

    # ----- Add Edge ----- #
    def add_edge(self):
        u, v, cap = self.from_entry.get(), self.to_entry.get(), self.capacity_entry.get()
        if not u or not v or not cap:
            messagebox.showerror("Input Error", "All fields must be filled!")
            return
        try:
            cap = float(cap)
            if cap < 0:
                raise ValueError
        except:
            messagebox.showerror("Input Error", "Capacity must be a non-negative number!")
            return
        self.edges.append((u, v, cap))
        self.edge_listbox.insert(tk.END, f"{u} → {v} | {cap}")
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
        if messagebox.askyesno("Clear All", "Remove all connections?"):
            self.edge_listbox.delete(0, tk.END)
            self.edges.clear()

    # ----- Solve in Thread ----- #
    def start_solve_thread(self):
        threading.Thread(target=self.solve_flow_worker, daemon=True).start()

    def solve_flow_worker(self):
        source, sink = self.source_entry.get(), self.sink_entry.get()
        if not source or not sink:
            self.root.after(0, lambda: messagebox.showerror("Input Error", "Start and End nodes must be specified!"))
            return

        try:
            max_flow, flow_dict, G = solve_max_flow(self.edges, source, sink)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            return

        self.root.after(0, lambda: self.update_ui_after_solve(source, sink, max_flow, flow_dict, G))

    # ----- Update UI safely ----- #
    def update_ui_after_solve(self, source, sink, max_flow, flow_dict, G):
        # Results
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, f"✅ Maximum flow from {source} to {sink} is {max_flow}\n\n")
        for u, flows in flow_dict.items():
            for v, f in flows.items():
                if f > 0:
                    self.result_text.insert(tk.END, f"• {f:.3f} units: {u} → {v}\n")

        # Draw base graph
        self.ax.clear()
        pos = nx.spring_layout(G, seed=42)
        nx.draw_networkx_nodes(G, pos, ax=self.ax, node_color='skyblue', node_size=1000)
        nx.draw_networkx_labels(G, pos, ax=self.ax, font_size=12)
        nx.draw_networkx_edges(G, pos, ax=self.ax, edge_color="lightgray", arrows=True, arrowsize=20)
        self.canvas.draw()

        # Animate edges
        edges = list(G.edges())
        self._animate_index = 0

        def animate_step():
            if self._animate_index >= len(edges):
                return
            u, v = edges[self._animate_index]
            flow = flow_dict.get(u, {}).get(v, 0)
            cap = G[u][v]['capacity']
            ratio = flow / cap if cap else 0

            nx.draw_networkx_edges(G, pos, edgelist=[(u, v)], ax=self.ax,
                                   edge_color=[plt.cm.Blues(ratio)],
                                   arrows=True, arrowsize=20, width=3)
            label = f"{flow:.3f}/{cap:.3f}" if isinstance(flow, float) or isinstance(cap, float) else f"{flow}/{cap}"
            nx.draw_networkx_edge_labels(G, pos, edge_labels={(u, v): label},
                                         ax=self.ax, font_color='darkblue')
            self.canvas.draw()

            self._animate_index += 1
            self.root.after(400, animate_step)

        animate_step()


# ---------------- Run ---------------- #
if __name__ == "__main__":
    root = tk.Tk()
    app = NetworkFlowApp(root)
    root.mainloop()
