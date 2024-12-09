import tkinter as tk
from tkinter import Text
from pymongo import MongoClient
from neo4j import GraphDatabase
#import re
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
#import scipy as sp
import random


# MongoDB and Neo4j connection details
MONGO_URI = "mongodb://localhost:27017"
NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "12341234")

def select_all(event):
    """Enable Ctrl+A to select all text in the entry box."""
    event.widget.select_range(0, tk.END)
    event.widget.icursor(tk.END)
    return "break"

def query_mongo(query):
    """Query MongoDB for the given property."""
    try:
        client = MongoClient(MONGO_URI)
        db = client["NoSQLProj"]  # Replace with your MongoDB database name
        collection = db["MoodleDB"]  # Replace with your MongoDB collection name
        
        # Query the MongoDB collection
        result = collection.find_one({"$or": [
            {"Entry": {"$regex": query, "$options": "i"}},
            {"Entry Name": {"$regex": query, "$options": "i"}},
            {"Protein names": {"$regex": query, "$options": "i"}},
            {"Gene Names": {"$regex": query, "$options": "i"}},
            {"Organism": query},
            {"Sequence": query},
            {"InterPro": {"$regex": query, "$options": "i"}}
        ]})
        
        if result:
            # Format and return the result
            return (f"MongoDB Result:\n"
                    f"Entry: {result.get('Entry', '')}\n"
                    f"Entry Name: {result.get('Entry Name', '')}\n"
                    f"Protein Names: {result.get('Protein names', '')}\n"
                    f"Gene Names: {result.get('Gene Names', '')}\n"
                    f"Organism: {result.get('Organism', '')}\n"
                    f"EC Number: {result.get('EC number', '')}\n"
                    f"InterPro: {result.get('InterPro', '')}")
        else:
            return "MongoDB Result: No data found for the given query."
    except Exception as e:
        return f"MongoDB Result: Connection failed - {e}"

def query_neo4j(query):
    """Query Neo4j for the given property."""
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
        with driver.session() as session:
            # Query the Neo4j database
            result = session.run(
                """
                MATCH (n)
                WHERE n.entry =~ '(?i).*' + $query + '.*' 
                      OR n.entryName =~ '(?i).*' + $query + '.*' 
                      OR n.geneName =~ '(?i).*' + $query + '.*' 
                      OR n.proteinNames =~ '(?i).*' + $query + '.*'
                RETURN n
                """, parameters={"query": query}  # Properly pass query parameter
            )
            record = result.single()
            if record:
                node = record["n"]
                # Format and return the result
                return (f"Neo4j Result:\n"
                        f"Entry: {node.get('entry', '')}\n"
                        f"Entry Name: {node.get('entryName', '')}\n"
                        f"Protein Name: {node.get('proteinNames', '')}\n"
                        f"Gene Name: {node.get('geneName', '')}\n"
                        f"EC Numbers: {node.get('ec_numbers', '')}\n"
                        f"InterPro: {node.get('interPro', '')}")
            else:
                return "Neo4j Result: No data found for the given query."
    except Exception as e:
        return f"Neo4j Result: Connection failed - {e}"
    
# Global variables for zoom and graph data
zoom_factor = 1.0
current_nodes, current_edges = set(), []

def update_statistics():
    """Update the statistics section with 5 random statements."""
    random_statements = [
        "Average interactions per protein with similarity > 0.8: 9.64",
        "Proteins which have the most number of relationships with similarity > 0.8: 293",
        "Protein with highest interactions with similarity > 0.8: K7T918, K7U6K6",
        "5 Most frequent EC number: 2.7.11.1 - 675, 2.3.2.27 - 459, 3.4.19.12 - 251, 3.6.4.13 - 213, 2.7.10.1 - 186",
        "Top organism in dataset: Mus musculus (Mouse)",
        "Proteins with no interactions (Similarity < 0.02): 4",
        "Proteins which have no relationships(Jacardian similarity=0): 0",
        "Mean similarity > 0.8: 0.97"
    ]
    
    # Randomly select 5 statements
    selected_stats = random.sample(random_statements, 10)
    
    # Update the statistics text widget
    stats_result.config(state="normal")
    stats_result.delete(1.0, tk.END)
    stats_result.insert(tk.END, "\n".join(selected_stats))
    stats_result.config(state="disabled")

def query_neo4j_graph(query):
    """Query Neo4j for graph data."""
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
        with driver.session() as session:
            # Fetch nodes and relationships for the graph
            # result = session.run(
            #     """
            #     MATCH (n)-[r]-(m)
            #     WHERE n.entry =~ '(?i).*' + $query + '.*' 
            #           OR n.entryName =~ '(?i).*' + $query + '.*' 
            #           OR n.proteinNames =~ '(?i).*' + $query + '.*'
            #           OR n.geneName =~ '(?i).*' + $query + '.*'
            #     RETURN n, r, m LIMIT 50
            #     """, parameters={"query": query}
            # )
            result = session.run(
                # """
                # MATCH (n) 
                # WHERE n.entry = $query
                # WITH n
                # MATCH (n)-[r1]-(b)
                # WITH n, r1, b
                # MATCH (b)-[r2]-(c)
                # RETURN DISTINCT n, r1, b, r2, c LIMIT 30
                # """, parameters={"query": query}
                """
                MATCH (n) 
                WHERE n.entry = $query
                WITH n
                MATCH (n)-[r1]-(b)
                WITH n, COLLECT(b) AS neighbors
                UNWIND neighbors AS b
                MATCH (b)-[r]-(c)
                WHERE c IN neighbors OR c = n
                RETURN DISTINCT n, r, b, c LIMIT 500
                """, parameters={"query": query}
            )
            nodes, edges = set(), []
            for record in result:
                n = record["n"]
                # m = record["m"]
                b = record["b"]
                c = record["c"]
                r = record["r"]
                # r1 = record["r1"]
                # r2 = record["r2"]
                nodes.add((n["entry"], n["entryName"]))
                #nodes.add((m["entry"], m["entryName"]))
                nodes.add((b["entry"], b.get("entryName", "Unknown")))
                nodes.add((c["entry"], c.get("entryName", "Unknown")))
                edges.append((b["entry"], c["entry"], r.get("weight", 1)))  # From b to c
                #edges.append((n["entry"], m["entry"], r["weight"] if "weight" in r else 1))
                # edges.append((n["entry"], b["entry"], r1.get("weight", 1)))  # From n to b
                # edges.append((b["entry"], c["entry"], r2.get("weight", 1)))  # From b to c
            return nodes, edges
    except Exception as e:
        print(f"Neo4j graph query failed: {e}")
        return set(), []
'''
def draw_graph(nodes, edges):
    
    global graph_canvas, zoom_factor

    # Clear existing graph
    for widget in right_frame.winfo_children():
        if isinstance(widget, FigureCanvasTkAgg):
            widget.get_tk_widget().destroy()

    # Create a NetworkX graph
    G = nx.DiGraph()
    for node in nodes:
        G.add_node(node[0], label=node[1])
    for edge in edges:
        G.add_edge(edge[0], edge[1], weight=edge[2])

    # Create a Matplotlib figure
    fig, ax = plt.subplots(figsize=(8 * zoom_factor, 6 * zoom_factor))
    pos = nx.spring_layout(G)  # Use spring layout for graph positioning

    # Draw the graph
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=500, node_color="skyblue")
    nx.draw_networkx_edges(G, pos, ax=ax, arrowstyle="->", arrowsize=20)
    nx.draw_networkx_labels(G, pos, ax=ax, labels={n: n for n in G.nodes})
    edge_labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=ax)

    ax.axis("off")  # Turn off the axis

    # Embed the Matplotlib figure in tkinter
    canvas = FigureCanvasTkAgg(fig, master=right_frame)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.grid(row=1, column=0, sticky="nsew")
    canvas.draw() 

    global canvas, zoom_factor

    # Clear existing graph
    for widget in right_frame.winfo_children():
        if isinstance(widget, FigureCanvasTkAgg):
            widget.get_tk_widget().destroy()

    # Create a NetworkX graph
    G = nx.DiGraph()
    for node in nodes:
        G.add_node(node[0], label=node[1])
    for edge in edges:
        G.add_edge(edge[0], edge[1], weight=edge[2])

    # Create a Matplotlib figure
    fig, ax = plt.subplots(figsize=(8 * zoom_factor, 6 * zoom_factor))
    pos = nx.spring_layout(G)  # Use spring layout for graph positioning

    # Draw the graph
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=500, node_color="skyblue")
    nx.draw_networkx_edges(G, pos, ax=ax, arrowstyle="->", arrowsize=20)
    nx.draw_networkx_labels(G, pos, ax=ax, labels={n: n for n in G.nodes})
    edge_labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=ax)

    ax.axis("off")  # Turn off the axis

    # Enable interactive scrolling and zooming
    def on_scroll(event):
        """Handle zooming via trackpad."""
        global zoom_factor
        if event.button == 'up':  # Scroll up
            zoom_factor += 0.1
        elif event.button == 'down':  # Scroll down
            zoom_factor = max(0.2, zoom_factor - 0.1)
        draw_graph(nodes, edges)  # Redraw graph with updated zoom factor

    fig.canvas.mpl_connect('scroll_event', on_scroll)  # Connect scroll event

    # Embed the Matplotlib figure in tkinter
    canvas = FigureCanvasTkAgg(fig, master=graph_canvas)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(fill=tk.BOTH, expand=True)
    canvas.draw()

    
    global graph_canvas, zoom_factor

    # Clear existing graph
    for widget in right_frame.winfo_children():
        if isinstance(widget, FigureCanvasTkAgg):
            widget.get_tk_widget().destroy()

    # Create a directed graph in NetworkX
    G = nx.DiGraph()  # Directed graph
    for node in nodes:
        G.add_node(node[0], label=node[1])
    for edge in edges:
        G.add_edge(edge[0], edge[1], weight=edge[2])

    # Create a Matplotlib figure
    fig, ax = plt.subplots(figsize=(8 * zoom_factor, 6 * zoom_factor))
    pos = nx.spring_layout(G)  # Spring layout for graph positioning

    # Draw the directed graph
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=500, node_color="skyblue")
    nx.draw_networkx_edges(G, pos, ax=ax, arrowstyle="->", arrowsize=20)
    nx.draw_networkx_labels(G, pos, ax=ax, labels={n: n for n in G.nodes})
    edge_labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=ax)

    ax.axis("off")  # Turn off the axis

    # Embed the Matplotlib figure in tkinter
    canvas = FigureCanvasTkAgg(fig, master=right_frame)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.grid(row=1, column=0, sticky="nsew")
    canvas.draw()
'''

def on_mousewheel(event):
    global zoom_factor
    if event.delta > 0:
        zoom_factor += 0.1  # Zoom in
    elif event.delta < 0:
        zoom_factor = max(0.1, zoom_factor - 0.1)  # Zoom out
    draw_graph(current_nodes, current_edges)


def draw_graph(nodes, edges):
    """Draw the graph using NetworkX and Matplotlib with better layout and navigation."""
    global graph_canvas, graph_toolbar, zoom_factor

    # Clear existing graph and toolbar
    for widget in right_frame.winfo_children():
        if isinstance(widget, FigureCanvasTkAgg) or isinstance(widget, NavigationToolbar2Tk):
            widget.destroy()

    # Create a NetworkX graph
    G = nx.DiGraph()
    for node in nodes:
        G.add_node(node[0], label=node[1])
    for edge in edges:
        G.add_edge(edge[0], edge[1], weight=edge[2])

    # Create a Matplotlib figure
    fig, ax = plt.subplots(figsize=(8 * zoom_factor, 6 * zoom_factor))
    pos = nx.kamada_kawai_layout(G)  # Use Kamada-Kawai layout for better organization

    # Draw the graph
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=500, node_color="skyblue", alpha=0.8)
    nx.draw_networkx_edges(G, pos, ax=ax, arrowstyle="->", arrowsize=10, edge_color="gray", alpha=0.7)
    nx.draw_networkx_labels(G, pos, ax=ax, labels={n: n for n in G.nodes}, font_size=8)
    edge_labels = nx.get_edge_attributes(G, "weight")
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=ax, font_size=6)

    ax.axis("off")  # Turn off the axis for a cleaner look

    # Embed the Matplotlib figure in tkinter
    canvas = FigureCanvasTkAgg(fig, master=right_frame)
    graph_canvas = canvas
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.grid(row=1, column=0, sticky="nsew")
    canvas_widget.bind("<MouseWheel>", on_mousewheel)  # For Windows
    canvas_widget.bind("<Button-4>", on_mousewheel)    # For Linux
    canvas_widget.bind("<Button-5>", on_mousewheel)    # For Linux

    canvas.draw()

    # Add Matplotlib toolbar for navigation
    toolbar_frame = tk.Frame(right_frame)
    toolbar_frame.grid(row=2, column=0, sticky="ew")
    graph_toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
    graph_toolbar.update()


def zoom_in():
    """Zoom in the graph."""
    global zoom_factor
    zoom_factor += 0.2
    draw_graph(current_nodes, current_edges)

def zoom_out():
    """Zoom out the graph."""
    global zoom_factor
    zoom_factor = max(0.2, zoom_factor - 0.2)
    draw_graph(current_nodes, current_edges)


def execute_query():
    """Execute the query on MongoDB and Neo4j and update the UI."""
    query = query_entry.get().strip()
    if not query:
        return
    
    # Query MongoDB
    mongo_result_text = query_mongo(query)
    mongo_result.config(state="normal")
    mongo_result.delete(1.0, tk.END)
    mongo_result.insert(tk.END, mongo_result_text)
    mongo_result.config(state="disabled")
    
    # Query Neo4j
    neo4j_result_text = query_neo4j(query)
    neo4j_result.config(state="normal")
    neo4j_result.delete(1.0, tk.END)
    neo4j_result.insert(tk.END, neo4j_result_text)
    neo4j_result.config(state="disabled")

    update_statistics()

    # Query Neo4j for graph data
    global current_nodes, current_edges
    current_nodes, current_edges = query_neo4j_graph(query)
    draw_graph(current_nodes, current_edges)


# Create the main window
root = tk.Tk()
root.title("Protein Query Interface")
root.geometry("1200x800")  # Set initial window size
root.minsize(800, 600)  # Set minimum window size

# Adjust the left and right frame proportions (40:60)
root.rowconfigure(0, weight=1)
root.columnconfigure(0, weight=40)  # Left frame weight
root.columnconfigure(1, weight=60)  # Right frame weight

# Create a frame for the left side
left_frame = tk.Frame(root, bd=2, relief=tk.SUNKEN)
left_frame.grid(row=0, column=0, sticky="nsew")
left_frame.columnconfigure(0, weight=1)
left_frame.rowconfigure([1, 2, 3], weight=1)  # Resize MongoDB, Neo4j, and statistics sections

# Create a frame for the right side (graph display)
right_frame = tk.Frame(root, bd=2, relief=tk.SUNKEN)
right_frame.grid(row=0, column=1, sticky="nsew")
right_frame.columnconfigure(0, weight=1)
right_frame.rowconfigure(1, weight=1)

# Add the input box for the query on the left frame
query_label = tk.Label(left_frame, text="Type in the protein or entry or gene name you want to query:")
query_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)

query_frame = tk.Frame(left_frame)
query_frame.grid(row=0, column=0, sticky="ew", padx=5)

query_entry = tk.Entry(query_frame, width=40)  # Adjust width of the query entry box
query_entry.grid(row=0, column=0, sticky="ew")
query_entry.bind("<Control-a>", select_all)  # Enable Ctrl+A to select all

search_button = tk.Button(query_frame, text="Search", command=execute_query)
search_button.grid(row=0, column=1, padx=5)

# Add MongoDB result section
mongo_label = tk.Label(left_frame, text="MongoDB Result:")
mongo_label.grid(row=1, column=0, sticky="w", padx=5)

mongo_result = Text(left_frame, wrap="word", height=10, state="disabled", width=50)  # Adjust width
mongo_result.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

# Add Neo4j result section
neo4j_label = tk.Label(left_frame, text="Neo4J Result:")
neo4j_label.grid(row=2, column=0, sticky="w", padx=5)

neo4j_result = Text(left_frame, wrap="word", height=10, state="disabled", width=50)  # Adjust width
neo4j_result.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)

# Add statistics section
stats_label = tk.Label(left_frame, text="Some statistics about the dataset:")
stats_label.grid(row=3, column=0, sticky="w", padx=5)

stats_result = Text(left_frame, wrap="word", height=10, state="disabled", width=50)  # Adjust width
stats_result.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)

# Add graph display section on the right
graph_label = tk.Label(right_frame, text="Neo4J Graph Display for the Query:")
graph_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)

# Add a canvas for displaying the graph (placeholder)
graph_canvas = tk.Canvas(right_frame, bg="white", bd=2, relief=tk.SUNKEN, width=400, height=400)  # Adjust width/height
graph_canvas.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

# Add zoom buttons
zoom_in_button = tk.Button(right_frame, text="+", font=("Arial", 12), width=2)
zoom_in_button.grid(row=2, column=0, sticky="e", padx=10, pady=5)

zoom_out_button = tk.Button(right_frame, text="-", font=("Arial", 12), width=2)
zoom_out_button.grid(row=2, column=0, sticky="w", padx=10, pady=5)

zoom_in_button.config(command=zoom_in)
zoom_out_button.config(command=zoom_out)


root.mainloop()
