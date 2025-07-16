import json
import pandas as pd
from io import StringIO
from tabulate import tabulate


def find_paths(data, target, current_path=None):
    """
    Recursively find all paths from the root to the target node in the JSON tree.
    Returns a list of paths (each path is a list of names from root to target).
    """
    if current_path is None:
        current_path = []  # Start with an empty path if not provided
    found_paths = []  # This will collect all found paths
    for name, details in data.get("children", {}).items():
        new_path = current_path + [name]  # Add this node to the current path
        if name == target:
            found_paths.append(new_path)  # If this is the target, save the path
        # Recursively search in children for more paths
        found_paths += find_paths(details, target, new_path)
    return found_paths  # Return all found paths


def city2target_paths(data, city, target_state):
    """
    For a given city and target_state, return all possible paths from the city up to the target_state.
    If target_state is missing, return all paths from root to city.
    If city is not found, return None.
    """
    # If no target_state, just return all paths to the city (for ambiguity check)
    if not target_state or pd.isna(target_state):
        parent_paths = find_paths(data, city)
        if not parent_paths:
            return None  # City not found
        return parent_paths  # All possible paths to the city
    # Otherwise, get all paths to the city
    parent_paths = find_paths(data, city)
    if not parent_paths:
        return None  # City not found
    results = []
    for path in parent_paths:
        # Only consider paths that include the target_state
        if target_state in path:
            idx = path.index(target_state)  # Where is the state in the path?
            city_idx = len(path) - 1        # Where is the city in the path? (always last)
            if idx <= city_idx:
                # Slice from state to city (inclusive)
                results.append(path[idx:city_idx+1])
    if not results:
        return None  # No valid path from city to target_state
    return results


def get_admin_level(data, path):
    """
    Traverse the JSON tree following the path, return 'admin_level' if found.
    """
    node = data
    for name in path:
        if 'children' in node and name in node['children']:
            node = node['children'][name]
        else:
            return None
    return node.get('admin_level')


def last_common_from_start(path1, path2):
    """
    Compare two paths from the start and return the last common element and its index.
    """
    min_len = min(len(path1), len(path2))  # Only compare up to the shortest path
    last_common = None
    last_idx = -1
    for i in range(min_len):
        if path1[i] == path2[i]:
            last_common = path1[i]  # Update last common node
            last_idx = i            # And its index
        else:
            break  # Stop at first difference
    return last_common, last_idx


def compute_expected_levels_for_all(df, data):
    """
    For each row in the DataFrame, compute:
    - expected_level: the admin_level of the deepest common ancestor between city_1/state_1 and city_2/state_2
    - is_ambiguous: 1 if a city with missing state is ambiguous (multiple or no matches in JSON), else 0
    Print the DataFrame in a formatted table.
    """
    expected_levels = []
    ambiguous_flags = []
    for idx, row in df.iterrows():
        city1 = row['city_1']
        state1 = row['state_1']
        city2 = row['city_2']
        state2 = row['state_2']
        # Get all possible paths for each city/state
        paths1 = city2target_paths(data, city1, state1)
        paths2 = city2target_paths(data, city2, state2)
        # --- Ambiguity check ---
        ambiguous = 0
        # If state is missing, check if city is ambiguous (multiple or no matches)
        if not state1 or pd.isna(state1):
            all_paths1 = find_paths(data, city1)
            # Ambiguous if city not found or found in multiple places
            if not all_paths1 or len(all_paths1) > 1:
                ambiguous = 1
        if not state2 or pd.isna(state2):
            all_paths2 = find_paths(data, city2)
            if not all_paths2 or len(all_paths2) > 1:
                ambiguous = 1
        ambiguous_flags.append(ambiguous)
        # --- Expected level computation ---
        # If no valid paths, treat as country level (Portugal, admin_level 2)
        if not isinstance(paths1, list):
            paths1 = [
                ['Portugal']
            ]
        if not isinstance(paths2, list):
            paths2 = [
                ['Portugal']
            ]
        max_level = None
        for p1 in paths1:
            for p2 in paths2:
                # Find the deepest common ancestor between the two paths
                common, idx_common = last_common_from_start(p1, p2)
                # If there is a common ancestor
                if common is not None:
                    # Get the admin_level for this ancestor
                    admin_level = get_admin_level(data, p1[:idx_common+1])
                    # Keep the highest (deepest) admin_level found
                    if admin_level is not None:
                        if (max_level is None) or (admin_level > max_level):
                            max_level = admin_level
        # If no common ancestor found, set to 2 (country level)
        if max_level is None:
            max_level = 2
        expected_levels.append(max_level)
    df['expected_level'] = expected_levels
    df['is_ambiguous'] = ambiguous_flags
    print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))


if __name__ == "__main__":
    json_file = "portugal.json"

    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    dados = """
    id_1 id_2 city_1 city_2 state_1 state_2
    1 2 valadares valadares viseu porto
    1 3 valadares valadares viseu
    4 5 valadares valadares
    7 1 "lugar que nao existe" valadares viseu
    1 8 valadares "sao pedro do sul" viseu viseu
    1 8 valadares "sao pedro do sul" viseu
    10 9 valadares "sao pedro do sul" "" viseu
    """
    # Usar StringIO para simular um ficheiro # TODO: Em vez de criar o data frame assim, usa um csv ou um xlsx
    df = pd.read_csv(StringIO(dados), sep=' ', header=0, engine='python', quotechar='"')
    # Preencher colunas ausentes com NaN
    df = df.reindex(columns=['id_1', 'id_2', 'city_1', 'city_2', 'state_1', 'state_2'])

    # compute_expected_level(df)

    # Compute expected_level for all rows
    compute_expected_levels_for_all(df, data)
