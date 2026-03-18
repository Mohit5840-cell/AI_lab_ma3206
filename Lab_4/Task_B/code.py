import collections
import itertools
import heapq
import math

# --- PARSING & GRAPH SETUP (From Task 1) ---
def parse_input(input_lines):
    food_costs = {}
    group_size = 1
    assignments = {} 
    
    for line in input_lines:
        parts = line.strip().split()
        if not parts: continue
        if parts[0] == 'C':
            food_costs[parts[1]] = int(parts[2])
        elif parts[0] == 'G':
            group_size = int(parts[1])
        elif parts[0] == 'A':
            a_id = 'A' + parts[1]
            in1, in2 = int(parts[2]), int(parts[3])
            outcome = int(parts[4])
            food = parts[5]
            assignments[a_id] = {'inputs': [in1, in2], 'outcome': outcome, 'food': food}
            
    outcome_to_assignment = {data['outcome']: a_id for a_id, data in assignments.items()}
    
    graph = collections.defaultdict(list)
    prereqs = collections.defaultdict(list)
    
    for a_id, data in assignments.items():
        for inp in data['inputs']:
            if inp in outcome_to_assignment:
                prereq_id = outcome_to_assignment[inp]
                graph[prereq_id].append(a_id)
                prereqs[a_id].append(prereq_id)
                
    return assignments, graph, prereqs, food_costs, group_size

def calculate_leaf_depths(assignments, graph):
    """Calculates the longest path from each node to a leaf for the heuristic."""
    depths = {}
    def get_depth(node):
        if node in depths: 
            return depths[node]
        if not graph[node]:
            depths[node] = 1
            return 1
        depths[node] = 1 + max(get_depth(neighbor) for neighbor in graph[node])
        return depths[node]
        
    for a in assignments:
        get_depth(a)
    return depths

# --- A* SEARCH IMPLEMENTATION ---
def menu_cost(menu_counts, food_costs):
    return sum(count * food_costs[food] for food, count in menu_counts.items())

def is_dominated(day, menu, pareto_front, food_keys):
    """
    Checks if a state is strictly worse than an already visited state.
    Prevents the search space from exploding with sub-optimal permutations.
    """
    for (v_day, v_menu) in pareto_front:
        if v_day <= day:
            # Check if v_menu is <= menu in all food types
            if all(v_menu.get(f, 0) <= menu.get(f, 0) for f in food_keys):
                return True
    return False

def astar_schedule(assignments, graph, prereqs, food_costs, group_size):
    all_tasks = set(assignments.keys())
    food_keys = list(food_costs.keys())
    depths = calculate_leaf_depths(assignments, graph)
    
    # Priority Queue Elements: 
    # (f_score, g_score, tie_breaker, current_day, completed_tasks_frozenset, max_menu_tuple, schedule)
    pq = []
    tie_breaker = 0
    
    initial_completed = frozenset()
    initial_menu = {f: 0 for f in food_keys}
    initial_menu_tuple = tuple(initial_menu[f] for f in food_keys)
    
    # Push initial state
    heapq.heappush(pq, (0, 0, tie_breaker, 0, initial_completed, initial_menu_tuple, []))
    
    # Visited tracks the Pareto front for each specific set of completed tasks
    # visited[completed_tasks] = list of (day, menu_dict)
    visited = collections.defaultdict(list)
    states_explored = 0
    
    while pq:
        f_score, g_score, _, current_day, completed, menu_tuple, schedule = heapq.heappop(pq)
        states_explored += 1
        
        # Convert tuple back to dict for easy logic
        current_max_menu = {f: menu_tuple[i] for i, f in enumerate(food_keys)}
        
        # GOAL CHECK
        if len(completed) == len(all_tasks):
            final_cost = current_day * menu_cost(current_max_menu, food_costs)
            return schedule, current_max_menu, current_day, final_cost, states_explored
            
        # Determine available tasks (prereqs met, not yet completed)
        available = []
        for task in all_tasks:
            if task not in completed:
                if all(p in completed for p in prereqs[task]):
                    available.append(task)
                    
        # Generate all valid daily combinations (subsets of size 1 to G)
        max_subset_size = min(group_size, len(available))
        for size in range(1, max_subset_size + 1):
            for daily_tasks in itertools.combinations(available, size):
                
                # 1. Update State 
                new_completed = completed.union(daily_tasks)
                new_day = current_day + 1
                
                # 2. Calculate today's menu requirement and the new global max menu
                today_menu_counts = collections.Counter([assignments[t]['food'] for t in daily_tasks])
                new_max_menu = {}
                for f in food_keys:
                    new_max_menu[f] = max(current_max_menu.get(f, 0), today_menu_counts.get(f, 0))
                
                # 3. Apply Pareto Pruning (Skip if we have reached this point more efficiently before)
                if is_dominated(new_day, new_max_menu, visited[new_completed], food_keys):
                    continue
                visited[new_completed].append((new_day, new_max_menu))
                
                # 4. Calculate Path Cost g(n)
                current_menu_cst = menu_cost(new_max_menu, food_costs)
                new_g = new_day * current_menu_cst
                
                # 5. Calculate Heuristic h(n)
                uncompleted = all_tasks - new_completed
                if uncompleted:
                    min_days_by_volume = math.ceil(len(uncompleted) / group_size)
                    min_days_by_depth = max(depths[t] for t in uncompleted)
                    predicted_additional_days = max(min_days_by_volume, min_days_by_depth)
                else:
                    predicted_additional_days = 0
                    
                new_h = predicted_additional_days * current_menu_cst
                new_f = new_g + new_h
                
                # 6. Push to Queue
                new_menu_tuple = tuple(new_max_menu[f] for f in food_keys)
                new_schedule = schedule + [list(daily_tasks)]
                
                tie_breaker += 1
                heapq.heappush(pq, (new_f, new_g, tie_breaker, new_day, new_completed, new_menu_tuple, new_schedule))

    return None, None, 0, 0, states_explored

# --- GREEDY COMPARISON ---
def format_menu(menu_dict):
    return "<" + ", ".join([f"{count}-{food}" for food, count in menu_dict.items() if count > 0]) + ">"

def run_task_2_comparison(input_text):
    lines = input_text.strip().split('\n')
    assignments, graph, prereqs, food_costs, group_size = parse_input(lines)
    
    print("==========================================")
    print(" TASK 2: A* SEARCH vs GREEDY OPTIMIZATION ")
    print("==========================================\n")
    
    print("Executing A* Search... (Finding absolute optimal)")
    opt_schedule, opt_menu, opt_days, opt_cost, states = astar_schedule(assignments, graph, prereqs, food_costs, group_size)
    
    print(f"\n--- A* OPTIMAL RESULTS ---")
    print(f"States Explored: {states}")
    for day, tasks in enumerate(opt_schedule, 1):
        print(f"  Day-{day}: {', '.join(tasks)}")
    print(f"\nFixed Global Menu: {format_menu(opt_menu)}")
    print(f"Cost per Day: {menu_cost(opt_menu, food_costs)}")
    print(f"Total Days: {opt_days}")
    print(f">>> FINAL TOTAL COST: {opt_cost} <<<")

# Sample Data from PDF
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
    run_task_2_comparison(sample_input)