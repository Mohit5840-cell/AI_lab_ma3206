from graphviz import Digraph

def generate_greedy_flowchart():
    # Create a new directed graph
    dot = Digraph(comment='Greedy Scheduling Algorithm', format='png')
    dot.attr(rankdir='TB', size='8,10', fontname='Helvetica')
    
    # --- DEFINE NODES (The shapes) ---
    # Ovals for Start/End
    dot.node('Start', 'Start', shape='oval', style='filled', fillcolor='#87CEEB')
    dot.node('End', 'End\n(Return Schedule & Total Cost)', shape='oval', style='filled', fillcolor='#90EE90')
    
    # Rectangles for Actions
    dot.node('Parse', 'Phase 1: Initialization\nParse Data & Build DAG\nCalculate initial In-Degrees', shape='box')
    dot.node('InitQ', 'Populate "Waiting Room"\n(Find all tasks where In-Degree == 0)', shape='box')
    
    dot.node('Sort', 'Phase 2: The Greedy Choice\nSort the Waiting Room based on strategy\n(e.g., Cheapest Food, Longest Path)', shape='box', style='filled', fillcolor='#E6E6FA')
    dot.node('Select', 'Phase 3: The Workday\nSelect top "G" tasks from the queue\nRemove them from Waiting Room', shape='box')
    dot.node('Execute', 'Log tasks to current Day\nAdd daily food cost to Total Cost', shape='box')
    
    dot.node('Update', 'Phase 4: Chain Reaction\nFor each completed task:\nSubtract 1 from its neighbors\' In-Degrees', shape='box')
    dot.node('Unlock', 'Did any neighbor hit In-Degree == 0?\nIf YES -> Add to Waiting Room', shape='box')
    
    # Diamond for Decisions
    dot.node('CheckLoop', 'Is the Waiting\nRoom empty?', shape='diamond', style='filled', fillcolor='#FFDAB9')

    # --- DEFINE EDGES (The arrows) ---
    dot.edge('Start', 'Parse')
    dot.edge('Parse', 'InitQ')
    dot.edge('InitQ', 'CheckLoop')
    
    # The Decision Branching
    dot.edge('CheckLoop', 'End', label=' YES (All tasks done)', fontcolor='green', fontname='Helvetica-Bold')
    dot.edge('CheckLoop', 'Sort', label=' NO (Tasks remaining)', fontcolor='red', fontname='Helvetica-Bold')
    
    # The Main Loop
    dot.edge('Sort', 'Select')
    dot.edge('Select', 'Execute')
    dot.edge('Execute', 'Update')
    dot.edge('Update', 'Unlock')
    
    # Loop back to the start of the next day
    dot.edge('Unlock', 'CheckLoop', label=' Start Next Day')

    # --- RENDER ---
    # This will save a file called 'greedy_flowchart.png' in your folder and open it.
    dot.render('greedy_flowchart', view=True)
    print("Flowchart generated successfully as 'greedy_flowchart.png'!")

if __name__ == '__main__':
    generate_greedy_flowchart()