import json
import pandas as pd
from io import StringIO
from tabulate import tabulate


def find_paths(data, target, current_path=None):
    if current_path is None:
        current_path = []

    found_paths = []

    for name, details in data.get("children", {}).items():
        new_path = current_path + [name]
        if name == target:
            found_paths.append(new_path)
        # Recursively search in children
        found_paths += find_paths(details, target, new_path)

    return found_paths


def city2target_paths(data, city, target_state):
    if not target_state or pd.isna(target_state):
        parent_paths = find_paths(data, city)
        if not parent_paths:
            return "city do not exist"
        # Return all paths from root to city
        return parent_paths

    parent_paths = find_paths(data, city)
    if not parent_paths:
        return "city do not exist"

    results = []
    for path in parent_paths:
        if target_state in path:
            idx = path.index(target_state)
            city_idx = len(path) - 1
            if idx <= city_idx:
                results.append(path[idx:city_idx+1])
    if not results:
        return (
            f"Nenhum caminho até o estado '{target_state}' "
            f"encontrado para a cidade '{city}'"
        )
    return results


def get_admin_level(data, path):
    # Traverse the JSON tree following the path, return 'admin_level' if found
    node = data
    for name in path:
        if 'children' in node and name in node['children']:
            node = node['children'][name]
        else:
            return None
    return node.get('admin_level')


def last_common_from_start(path1, path2):
    # Compare from the start, return last common element and its index
    min_len = min(len(path1), len(path2))
    last_common = None
    last_idx = -1
    for i in range(min_len):
        if path1[i] == path2[i]:
            last_common = path1[i]
            last_idx = i
        else:
            break
    return last_common, last_idx


def compute_expected_levels_for_all(df, data):
    expected_levels = []
    ambiguous_flags = []
    for idx, row in df.iterrows():
        city1 = row['city_1']
        state1 = row['state_1']
        city2 = row['city_2']
        state2 = row['state_2']
        paths1 = city2target_paths(data, city1, state1)
        paths2 = city2target_paths(data, city2, state2)
        # Ambiguity check
        ambiguous = 0
        # Check for city_1
        if not state1 or pd.isna(state1):
            all_paths1 = find_paths(data, city1)
            if not all_paths1 or len(all_paths1) > 1:
                ambiguous = 1
        # Check for city_2
        if not state2 or pd.isna(state2):
            all_paths2 = find_paths(data, city2)
            if not all_paths2 or len(all_paths2) > 1:
                ambiguous = 1
        ambiguous_flags.append(ambiguous)
        # If error message, set paths to [['Portugal']] so admin_level 2 is used
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
                common, idx_common = last_common_from_start(p1, p2)
                if common is not None:
                    admin_level = get_admin_level(data, p1[:idx_common+1])
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
