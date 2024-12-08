import tkinter as tk
from tkinter import Text
from pymongo import MongoClient
from neo4j import GraphDatabase
#import re
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

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

    # Query Neo4J for graph data
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

root.mainloop()
