from collections import deque
from uuid import UUID

def sort_tasks_topologically(tasks):
    # 1. Map tasks by ID and initialize in-degree counts
    task_map = {t.id: t for t in tasks}
    in_degree = {t.id: 0 for t in tasks}
    adj = {t.id: [] for t in tasks}

    # 2. Build the adjacency list (who depends on whom)
    for t in tasks:
        for dep in t.dependencies:
            # dep is the parent, t is the child
            adj[dep.id].append(t.id)
            in_degree[t.id] += 1

    # 3. Find tasks with no dependencies (Starting nodes)
    queue = deque([t_id for t_id, count in in_degree.items() if count == 0])
    sorted_tasks = []

    while queue:
        u_id = queue.popleft()
        sorted_tasks.append(task_map[u_id])
        
        for v_id in adj[u_id]:
            in_degree[v_id] -= 1
            if in_degree[v_id] == 0:
                queue.append(v_id)

    return sorted_tasks