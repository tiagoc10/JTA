import json
from io import StringIO
import pandas as pd


def find_paths(data, target_city, current_path=None):
    '''
        Required recursive search
    '''
    found_paths = []
    if current_path is None:
        current_path = []  # Start with an empty path if not provided
    for name, details in data.get("children", {}).items():
        new_path = current_path + [name]
        if name == target_city:
            found_paths.append(new_path)
        found_paths += find_paths(details, target_city, new_path)

    return found_paths


def compare_city_paths(target_state1, target_state2, all_city_paths1, all_city_paths2):
    equal_index = []
    is_ambiguous = False

    if not pd.isna(target_state1) and not pd.isna(target_state2):
        is_ambiguous = False
        path1 = next((path for path in all_city_paths1 if target_state1 in path), None)
        city_state_target1 = ['Portugal'] + path1

        path2 = next((path for path in all_city_paths2 if target_state2 in path), None)
        city_state_target2 = ['Portugal'] + path2

        min_len = min(len(city_state_target1), len(city_state_target2))
        if len(city_state_target1) == len(city_state_target2):
            min_len -= 1  # Ignorar último nível (freguesia)

        city_state_target_min = min(city_state_target1, city_state_target2)
        city_state_target_max = max(city_state_target1, city_state_target2)

        for i in range(min_len):
            if city_state_target_min[i] == city_state_target_max[i]:
                equal_index.append(i)

    elif (pd.isna(target_state1) and not pd.isna(target_state2)) or (pd.isna(target_state2) and not pd.isna(target_state1)):
        if pd.isna(target_state1):
            known_target = target_state2
            known_paths = all_city_paths2
            unknown_paths = all_city_paths1
        else:
            known_target = target_state1
            known_paths = all_city_paths1
            unknown_paths = all_city_paths2

        known_path = next((path for path in known_paths if known_target in path), None)
        known_path = ['Portugal'] + known_path
        unknown_paths = [['Portugal'] + path for path in unknown_paths]

        is_ambiguous = len(unknown_paths) > 1
        equal_index = []

        for path in unknown_paths:
            min_len = min(len(known_path), len(path))
            city_state_target_min = min(known_path, path)
            path_max = max(known_path, path)
            for i in range(min_len):
                if city_state_target_min[i] == path_max[i]:
                    equal_index.append(i)

    elif pd.isna(target_state1) and pd.isna(target_state2):
        all_city_paths1 = [['Portugal'] + path for path in all_city_paths1]
        all_city_paths2 = [['Portugal'] + path for path in all_city_paths2]
        is_ambiguous = len(all_city_paths1) > 1 or len(all_city_paths2) > 1

        for path1 in all_city_paths1:
            for path2 in all_city_paths2:
                min_len = min(len(path1), len(path2))
                city_state_target_min = min(path1, path2)
                city_state_target_max = max(path1, path2)
                for i in range(min_len):
                    if city_state_target_min[i] == city_state_target_max[i]:
                        equal_index.append(i)

    return equal_index, is_ambiguous, city_state_target_min


def city2target_paths(df, data):

    is_ambiguous = False

    for idx, row in df.iterrows():
        city1 = row['city_1']
        target_state1 = row['state_1']
        city2 = row['city_2']
        target_state2 = row['state_2']

        # Find all paths for city1 and city2
        all_city_paths1 = find_paths(data, city1)
        all_city_paths2 = find_paths(data, city2)

        if (not all_city_paths1 and all_city_paths2) or (all_city_paths1 and not all_city_paths2):  # Verificar se a lista está vazia
            expected_level = 2
            is_ambiguous = False
            df.loc[idx, 'expected_level'] = expected_level
            df.loc[idx, 'is_ambiguous'] = 1 if is_ambiguous else 0
            # print(expected_level)
        elif not all_city_paths1 and not all_city_paths2:
            # Acho que a ideia acaba por ser esta. Se não é passado nenhuma cidade e é passado apenas o estado, então o maior nível o país
            expected_level = 2
            is_ambiguous = False  # Acho que não é ambíguo. Se só é passado o estado, então é o país
            df.loc[idx, 'expected_level'] = expected_level
            df.loc[idx, 'is_ambiguous'] = 1 if is_ambiguous else 0
        else:  # TODO: Cria uma rotina para tudo o que está neste else. Recebe entrada o target_state1 e target_state2
            equal_index, is_ambiguous, city_state_target_min = compare_city_paths(
                target_state1, target_state2, all_city_paths1, all_city_paths2)

            expected_level = get_admin_level(data, city_state_target_min[:max(equal_index)+1])
            df.loc[idx, 'expected_level'] = expected_level
            df.loc[idx, 'is_ambiguous'] = 1 if is_ambiguous else 0
    return df


def get_admin_level(data, path):
    """
    Traverse the JSON tree following the path, return 'admin_level' at the end of the path.
    """

    node = data
    # Remove 'Portugal' if it's the first element. Which it is
    if path and path[0] == 'Portugal':    # TODO: Não fazer assim.. Chegar mesmo ao admin_level=2 logo pelo primeiro
        path = path[1:]

    if len(path) > 0:
        for name in path:
            if 'children' in node and name in node['children']:
                node = node['children'][name]
                admin_level = node.get('admin_level')
    else:
        return 2  # Significa que path é [] porque só tinha 'Portugal', então é 2

    return admin_level


if __name__ == "__main__":
    json_file = "portugal.json"

    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    dataframe = """id_1;id_2;city_1;city_2;state_1;state_2
    1;2;valadares;valadares;viseu;porto
    1;3;valadares;valadares;viseu;
    4;5;valadares;valadares;;
    7;1;"lugar que nao existe";valadares;viseu;
    1;8;valadares;"sao pedro do sul";viseu;viseu
    1;8;valadares;"sao pedro do sul";viseu;
    10;9;valadares;"sao pedro do sul";;viseu
    12;13;;;Porto;Porto
    """

    df = pd.read_csv(StringIO(dataframe), sep=';', header=0)
    df = df.reindex(columns=['id_1', 'id_2', 'city_1', 'city_2', 'state_1', 'state_2'])

    # print(df)
    df = city2target_paths(df, data)
    print(df)
