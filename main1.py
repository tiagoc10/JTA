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
            raise ValueError(f"No cities provided:\nCity 1: {city1} (State: {target_state1}) | City 2: {city2} (State: {target_state2})")  # TODO: Verificar isto
        else:
            if not pd.isna(target_state1) and not pd.isna(target_state2):
                is_ambiguous = False
                path1 = next((path for path in all_city_paths1 if target_state1 in path), None)
                city_state_target1 = ['Portugal'] + path1
                # print(city_state_target1)

                path2 = next((path for path in all_city_paths2 if target_state2 in path), None)
                city_state_target2 = ['Portugal'] + path2
                # print(city_state_target2)

                equal_index = []
                min_len = min(len(city_state_target1), len(city_state_target2))
                if len(city_state_target1) == len(city_state_target2):
                    min_len -= 1  # Ignora último nível (é a freguesia) Já que significa que a cidade referenciada é o último nivel possível que é a freguesia
                city_state_target_min = min(city_state_target1, city_state_target2)
                city_state_target_max = max(city_state_target1, city_state_target2)
                for i in range(min_len):
                    if city_state_target_min[i] == city_state_target_max[i]:
                        equal_index.append(i)
                print("done")

            elif pd.isna(target_state2) and not pd.isna(target_state1):
                path1 = next((path for path in all_city_paths1 if target_state1 in path), None)
                city_state_target1 = ['Portugal'] + path1
                # print(city_state_target1)

                # all_city_paths2
                all_city_paths2 = [['Portugal'] + path for path in all_city_paths2]  # Acrescentar 'Portugal' em cada linha subarray
                is_ambiguous = True if len(all_city_paths2) > 1 else False
                # print(all_city_paths2)
                equal_index = []

                for path in all_city_paths2:
                    min_len = min(len(city_state_target1), len(path))  # Inclui freguesia
                    city_state_target_min = min(city_state_target1, path)
                    city_state_target_max = max(city_state_target1, path)
                    for i in range(min_len):
                        if city_state_target_min[i] == city_state_target_max[i]:
                            equal_index.append(i)
                # print(f'equal_index: {equal_index}')

            elif pd.isna(target_state1) and not pd.isna(target_state2):
                path2 = next((path for path in all_city_paths2 if target_state2 in path), None)
                city_state_target2 = ['Portugal'] + path2
                # print(city_state_target2)

                # all_city_paths1
                all_city_paths1 = [['Portugal'] + path for path in all_city_paths1]  # Acrescentar 'Portugal' em cada linha subarray
                is_ambiguous = True if len(all_city_paths1) > 1 else False
                # print(all_city_paths1)
                equal_index = []
                for path in all_city_paths1:
                    min_len = min(len(city_state_target2), len(path))  # Inclui freguesia
                    city_state_target_min = min(city_state_target2, path)
                    city_state_target_max = max(city_state_target2, path)
                    for i in range(min_len):
                        if city_state_target_min[i] == city_state_target_max[i]:
                            equal_index.append(i)
                # print(f'equal_index: {equal_index}')

            elif pd.isna(target_state1) and pd.isna(target_state2):
                all_city_paths1 = [['Portugal'] + path for path in all_city_paths1]  # Acrescentar 'Portugal' em cada linha subarray
                # print(all_city_paths1)

                all_city_paths2 = [['Portugal'] + path for path in all_city_paths2]  # Acrescentar 'Portugal' em cada linha subarray
                # print(all_city_paths2)

                is_ambiguous = True if len(all_city_paths1) > 1 or len(all_city_paths2) > 1 else False

                equal_index = []
                for path1 in all_city_paths1:
                    for path2 in all_city_paths2:
                        min_len = min(len(path1), len(path2))  # Inclui freguesia
                        city_state_target_min = min(path1, path2)  # Inclui freguesia
                        city_state_target_max = max(path1, path2)  # Inclui freguesia
                        for i in range(min_len):
                            if city_state_target_min[i] == city_state_target_max[i]:
                                equal_index.append(i)
                # print(f'equal_index: {equal_index}')

            relevant_index = max(equal_index)
            # Acho que é indiferente ser city_state_target1 ou city_state_target2...
            # Estás a ver onde são iguais
            # relevant_value = city_state_target[relevant_index]
            # print(relevant_index)
            # print(relevant_value)

            expected_level = get_admin_level(data, city_state_target_min[:relevant_index+1])
            # print("expected_level")
            # print(expected_level)

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
