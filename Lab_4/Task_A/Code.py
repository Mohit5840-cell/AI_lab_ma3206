import collections
import networkx as nx
import matplotlib.pyplot as plt
import collections

# ... [Keep your existing parse_input, calculate_depths, and greedy_schedule functions here] ...

def get_topological_layers(graph, base_in_degree, assignments):
    """
    Calculates the generation/layer of each node from the starting point.
    Assignments with 0 prerequisites are Layer 0. Their immediate children are Layer 1, etc.
    """
    layers = {}
    in_degree = base_in_degree.copy()
    
    # Start with all tasks that have no prerequisites
    queue = [a_id for a_id, deg in in_degree.items() if deg == 0]
    layer_num = 0
    
    while queue:
        next_queue = []
        for a_id in queue:
            layers[a_id] = layer_num
            # Look at subsequent tasks
            for neighbor in graph[a_id]:
                in_degree[neighbor] -= 1
                # If all prerequisites for the neighbor are now met, queue it for the next layer
                if in_degree[neighbor] == 0:
                    next_queue.append(neighbor)
        queue = next_queue
        layer_num += 1
        
    return layers


def visualize_graph(graph, assignments, in_degree):
    """
    Draws a Top-Down hierarchical representation of the DAG, 
    while forcing entirely separate task chains to stay apart visually.
    """
    import networkx as nx
    import matplotlib.pyplot as plt
    
    G = nx.DiGraph()
    
    # Get the proper top-down layers
    layers = get_topological_layers(graph, in_degree, assignments)
    
    for a_id in assignments.keys():
        G.add_node(a_id, layer=layers[a_id])
        
    for prereq_id, neighbors in graph.items():
        for dependent_id in neighbors:
            G.add_edge(prereq_id, dependent_id)
            
    plt.figure(figsize=(14, 8)) # Made slightly wider to accommodate spacing
    
    # --- NEW LOGIC: Separate Isolated Components ---
    pos = {}
    x_offset = 0
    padding = 1.5  # Adjust this value to increase/decrease the gap between chains
    
    # nx.weakly_connected_components finds fully isolated sub-trees (e.g. A4 -> A8)
    # We iterate through each isolated family one by one.
    for comp in nx.weakly_connected_components(G):
        sub_G = G.subgraph(comp)
        
        # 1. Calculate layered layout just for this specific family
        sub_pos = nx.multipartite_layout(sub_G, subset_key="layer")
        
        # 2. Rotate to Top-Down
        rotated_pos = {n: (y, -x) for n, (x, y) in sub_pos.items()}
        
        # 3. Find the width of this family so we know how much to shift it
        min_x = min(p[0] for p in rotated_pos.values())
        max_x = max(p[0] for p in rotated_pos.values())
        
        # 4. Shift all X-coordinates for this family to the right
        shift = x_offset - min_x
        for n in rotated_pos:
            pos[n] = (rotated_pos[n][0] + shift, rotated_pos[n][1])
            
        # 5. Increase the starting offset for the NEXT family by the width of this one
        x_offset += (max_x - min_x) + padding
        
    # --- DRAWING ---
    nx.draw_networkx_nodes(G, pos, 
                           node_size=1400, 
                           node_color='#87CEEB', 
                           edgecolors='black',
                           linewidths=2)
    
    nx.draw_networkx_edges(G, pos, 
                           edgelist=G.edges(), 
                           arrowstyle='-|>', 
                           arrowsize=25, 
                           edge_color='gray')
    
    nx.draw_networkx_labels(G, pos, 
                            font_size=12, 
                            font_weight='bold', 
                            font_family="sans-serif")
    
    plt.title("Isolated Component Dependency Graph", size=16, fontweight='bold', pad=20)
    plt.axis("off")
    plt.tight_layout()
    plt.show()
    

def parse_input(input_lines):
    """
    Parses the custom text format into usable data structures.
    """
    food_costs = {}
    group_size = 1
    assignments = {} # Maps assignment ID -> {'inputs': [], 'outcome': int, 'food': str}
    
    for line in input_lines:
        parts = line.strip().split()
        if not parts:
            continue
        
        # Parse Food Costs
        if parts[0] == 'C':
            food_costs[parts[1]] = int(parts[2])
            
        # Parse Group Size
        elif parts[0] == 'G':
            group_size = int(parts[1])
            
        # Parse Assignments (Format: A <id> <in1> <in2> <outcome> <food>)
        elif parts[0] == 'A':
            a_id = 'A' + parts[1]
            # Handling variable number of inputs before the outcome and food
            # Based on the sample, it's A id in1 in2 outcome food
            in1, in2 = int(parts[2]), int(parts[3])
            outcome = int(parts[4])
            food = parts[5]
            assignments[a_id] = {'inputs': [in1, in2], 'outcome': outcome, 'food': food}
            
    # Map each outcome to the assignment that produces it
    outcome_to_assignment = {data['outcome']: a_id for a_id, data in assignments.items()}
    
    # Build Directed Acyclic Graph (DAG) for dependencies
    graph = collections.defaultdict(list)
    in_degree = {a_id: 0 for a_id in assignments}
    
    for a_id, data in assignments.items():
        for inp in data['inputs']:
            if inp in outcome_to_assignment:
                prereq_id = outcome_to_assignment[inp]
                graph[prereq_id].append(a_id) # Edge from prerequisite to current assignment
                in_degree[a_id] += 1          # Increment unmet prerequisites count
                
    return assignments, graph, in_degree, food_costs, group_size


def calculate_depths(graph, assignments):
    """
    Calculates the longest path (dependency depth) from each node to a leaf node.
    Used for the 'Critical Path' strategy to find bottlenecks.
    """
    depths = {a_id: 0 for a_id in assignments}
    
    def dfs(node):
        if not graph[node]:
            return 0
        max_depth = 0
        for neighbor in graph[node]:
            max_depth = max(max_depth, 1 + dfs(neighbor))
        depths[node] = max_depth
        return max_depth
        
    for a_id in assignments:
        dfs(a_id)
    return depths


def greedy_schedule(assignments, graph, base_in_degree, food_costs, group_size, strategy_name):
    """
    Core scheduling engine that applies different greedy sorting strategies 
    to the pool of currently available assignments.
    """
    # Create a fresh copy of in-degrees for this simulation run
    in_degree = base_in_degree.copy()
    
    # Initialize the queue with assignments that have 0 prerequisites
    available = [a_id for a_id, deg in in_degree.items() if deg == 0]
    
    depths = calculate_depths(graph, assignments)
    schedule = []
    total_cost = 0
    
    while available:
        # ---------------------------------------------------------
        # APPLYING THE GREEDY HEURISTICS
        # ---------------------------------------------------------
        
        if strategy_name == "Cheapest Food First":
            # STRATEGY 1: Minimize Immediate Financial Cost
            # Sorts available tasks primarily by the cost of their required food (ascending).
            # Tie-breaker: Alphabetical order of the assignment ID.
            available.sort(key=lambda x: (food_costs[assignments[x]['food']], x))
            
        elif strategy_name == "Deepest Critical Path":
            # STRATEGY 2: Unlock Bottlenecks (Longest Path)
            # Prioritizes tasks that have the longest chain of dependencies ahead of them.
            # Sorts by depth descending (using a negative sign).
            available.sort(key=lambda x: (-depths[x], x))
            
        elif strategy_name == "Most Immediate Successors":
            # STRATEGY 3: Maximize Immediate Unlocks (Out-Degree)
            # Prioritizes tasks that directly act as prerequisites for the highest 
            # number of subsequent tasks, aiming to expand the 'available' pool quickly.
            available.sort(key=lambda x: (-len(graph[x]), x))
            
        elif strategy_name == "Highest Food Frequency":
            # STRATEGY 4: Group Similar Diets
            # Counts how many times each food type appears in the CURRENT available pool.
            # Prioritizes tasks whose food type is most abundant right now, encouraging
            # homogeneous daily menus which could scale well with bulk discount rules.
            food_counts = collections.Counter([assignments[x]['food'] for x in available])
            available.sort(key=lambda x: (-food_counts[assignments[x]['food']], food_costs[assignments[x]['food']], x))

        # ---------------------------------------------------------
        # EXECUTE THE DAY's PLAN
        # ---------------------------------------------------------
        
        # Pick up to 'group_size' assignments from the top of the sorted queue
        daily_assignments = available[:group_size]
        available = available[group_size:] # Remove selected from available pool
        
        schedule.append(daily_assignments)
        
        # Calculate the actual daily food cost
        daily_cost = sum(food_costs[assignments[a_id]['food']] for a_id in daily_assignments)
        total_cost += daily_cost
        
        # Update the graph dependencies
        for a_id in daily_assignments:
            for neighbor in graph[a_id]:
                in_degree[neighbor] -= 1
                # If a neighbor's prerequisites are all met, add it to the available queue
                if in_degree[neighbor] == 0:
                    available.append(neighbor)
                    
    return schedule, total_cost


def run_all_strategies(input_text):
    """
    Main driver function to execute and compare all implemented strategies.
    """
    lines = input_text.strip().split('\n')
    assignments, graph, in_degree, food_costs, group_size = parse_input(lines)
    lines = input_text.strip().split('\n')
    assignments, graph, in_degree, food_costs, group_size = parse_input(lines)
    
   # Pass in_degree as the third argument
    print("Generating Graph Visualization... (Close the window to continue to the scheduling output)")
    visualize_graph(graph, assignments, in_degree)
    
    strategies = [
        "Cheapest Food First", 
        "Deepest Critical Path", 
        "Most Immediate Successors",
        "Highest Food Frequency"
    ]
    
    print(f"==========================================")
    print(f" RUNNING SCHEDULER (Group Size: {group_size})")
    print(f"==========================================\n")
    
    for strategy in strategies:
        print(f"--- Strategy: {strategy} ---")
        schedule, total_cost = greedy_schedule(assignments, graph, in_degree, food_costs, group_size, strategy)
        
        for day, tasks in enumerate(schedule, 1):
            tasks_str = ", ".join(tasks)
            
            # Format the daily menu required for the output
            menu_counts = collections.Counter([assignments[t]['food'] for t in tasks])
            menu_str = ", ".join([f"{count}-{food}" for food, count in menu_counts.items()])
            daily_cost = sum(food_costs[assignments[t]['food']] for t in tasks)
            
            print(f"  Day-{day}: {tasks_str}")
            print(f"  Menu: <{menu_str}>")
            print(f"  Cost: {daily_cost}")
            
        print(f">>> Total Days Required: {len(schedule)}")
        print(f">>> Total Food Cost: {total_cost}\n")


# Sample Input Data from Page 4 of the Assignment PDF
sample_input = """
C TC 1
C DF 1
C PM 1
C GJ 1
G 2
A 1 1 3 7 TC
A 2 4 2 8 TC
A 3 1 3 9 TC
A 4 2 3 10 PM
A 5 7 8 11 TC
A 6 4 6 12 TC
A 7 6 9 13 PM
A 8 10 5 14 GJ
A 9 1 11 15 DF
A 10 3 12 16 TC
A 11 15 16 17 DF
"""

if __name__ == "__main__":
    run_all_strategies(sample_input)