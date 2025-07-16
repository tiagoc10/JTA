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


def city2target_path(df, city, target_state):
    for index, row in df[5:6].iterrows():
        city = row[city]
        target_state = row[target_state]

        parent_paths = find_paths(data, city)

        if not parent_paths:
            print(f"Nenhum caminho encontrado para a cidade '{city}'")
            return None

        if pd.isna(target_state) or not target_state:
            # Se não foi passado um estado, devolve todos os caminhos possíveis da cidade até Portugal
            all_paths = []
            for path in parent_paths:
                reversed_path = list(reversed(path)) + ['Portugal']
                print(reversed_path)
                all_paths.append(reversed_path)
            return all_paths

        else:
            found_any = False
            for path in parent_paths:
                reversed_path = list(reversed(path))
                if target_state.lower() in [p.lower() for p in reversed_path]:
                    found_any = True
                    path_array = reversed_path[:reversed_path.index(target_state) + 1] + ['Portugal']
                    # print(path_array)
                    return path_array
            if not found_any:
                print(f"Nenhum caminho até o estado '{target_state}' encontrado para a cidade '{city}'")


def compute_expected_level(df):
    # Comparar
    city = 'city_1'
    target_state = 'state_1'
    locs_city1 = city2target_path(df, city, target_state)
    # print(locs_city1)
    city = 'city_2'
    target_state = 'state_2'
    locs_city2 = city2target_path(df, city, target_state)
    print(locs_city2)
    # pos = find_last_common_from_end_ignore_first(locs_city1, locs_city2)
    # expected_level = expected_level_associated.get(pos, None)

    # if not expected_level:
    #     expected_level = 2
    # df["expected_level"] = expected_level
    # print(f"expected_level: {expected_level}")

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

    compute_expected_level(df)
