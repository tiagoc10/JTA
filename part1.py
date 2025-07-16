import json
import pandas as pd
from io import StringIO

expected_level_associated = {
    1: 8,
    2: 7,
    3: 2
}


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


def get_parents(data, target):
    paths = find_paths(data, target)
    return [path[:-1] for path in paths]


def find_last_common_from_end_ignore_first(list1, list2):
    # Ignorar o primeiro elemento
    sub1 = list1[1:]
    sub2 = list2[1:]

    idx1 = len(sub1) - 1
    idx2 = len(sub2) - 1
    last_common_idx = -1

    while idx1 >= 0 and idx2 >= 0 and sub1[idx1] == sub2[idx2]:
        last_common_idx = idx1 + 1  # +1 para ajustar o índice original (pois ignoramos o primeiro)
        idx1 -= 1
        idx2 -= 1

    return last_common_idx


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


def compute_expected_level(df):
    city = 'city_1'
    target_state = 'state_1'
    res1 = city2target_paths(data, df[city][0], df[target_state][0])
    print(f"Paths for {df[city][0]} to {df[target_state][0]}: {res1}")
    city = 'city_2'
    target_state = 'state_2'
    res2 = city2target_paths(data, df[city][0], df[target_state][0])
    print(f"Paths for {df[city][0]} to {df[target_state][0]}: {res2}")


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
    1 8 valadares "sao pedro do sul viseu" viseu
    1 8 valadares "sao pedro do sul viseu"
    10 9 valadares "sao pedro do sul" viseu
    """
    # Usar StringIO para simular um ficheiro # TODO: Em vez de criar o data frame assim, usa um csv ou um xlsx
    df = pd.read_csv(StringIO(dados), sep=' ', header=0, engine='python', quotechar='"')
    # Preencher colunas ausentes com NaN
    df = df.reindex(columns=['id_1', 'id_2', 'city_1', 'city_2', 'state_1', 'state_2'])

    # compute_expected_level(df)

    # Test row 2 from dados (index 1)
    row = df.iloc[4]
    city = row['city_2']
    target_state = row['state_2']
    result = city2target_paths(data, city, target_state)
    print(f"Paths for {city} to {target_state}: {result}")
