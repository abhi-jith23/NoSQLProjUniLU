import tkinter as tk
from tkinter import Text
from pymongo import MongoClient
from neo4j import GraphDatabase

# MongoDB and Neo4j connection details
MONGO_URI = "mongodb://localhost:27017"
NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "12341234")

def select_all(event):
    """Enable Ctrl+A to select all text in the entry box."""
    event.widget.select_range(0, tk.END)
    event.widget.icursor(tk.END)
    return "break"

def execute_query():
    """Placeholder function for the Search button."""
    print(f"Executing query: {query_entry.get()}")

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
