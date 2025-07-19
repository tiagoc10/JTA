import json
from io import StringIO
import pandas as pd


def find_paths(data, target_city, current_path=None):
    """
    Recursively find all paths in the JSON structure that lead to the target\
        city.
    Args:
        data (dict): The JSON data structure.
        target_city (str): The city to find paths to.
        current_path (list): The current path being traversed (used for\
            recursion).
    Returns:
        list: A list of paths (as lists of city names) that lead to the\
            target city.
    """
    found_paths = []
    if current_path is None:
        current_path = []

    for name, details in data.get("children", {}).items():
        current_path.append(name)
        if name == target_city:
            found_paths.append(list(current_path))
        found_paths.extend(find_paths(details, target_city, current_path))
        current_path.pop()

    return found_paths


def compare_city_paths(target_state1, target_state2, all_city_paths1,
                       all_city_paths2):
    """
    Compare paths of two cities to determine the common path to their\
        respective states.
    Args:
        target_state1 (str): The target state for the first city.
        target_state2 (str): The target state for the second city.
        all_city_paths1 (list): All paths for the first city.
        all_city_paths2 (list): All paths for the second city.
    Returns:
        - equal_index (list): Indices where the paths are equal.
        - is_ambiguous (bool): Whether the paths are ambiguous.
        - city_state_target_min (list): The minimum path to the target state.
    """
    equal_index = []
    is_ambiguous = False
    city_state_target_min = []

    target_state1_nan = pd.isna(target_state1)
    target_state2_nan = pd.isna(target_state2)

    if not target_state1_nan and not target_state2_nan:
        is_ambiguous = False

        # Todos os caminhos com o target_state1
        paths1 = [path for path in all_city_paths1 if target_state1 in path]
        # Todos os caminhos com o target_state2
        paths2 = [path for path in all_city_paths2 if target_state2 in path]

        if len(paths1) > 1:  # Exemplo do ponta do sol-madeira entende-se
            paths1 = [max(paths1, key=len)]  # Get the longest path
            is_ambiguous = True
        if len(paths2) > 1:
            paths2 = [max(paths2, key=len)]  # Get the longest path
            is_ambiguous = True

        path1 = next((path for path in paths1 if target_state1 in path), None)
        path2 = next((path for path in paths2 if target_state2 in path), None)

        if path1 is None and path2:
            return [], True, 'path1 not found'
        elif path2 is None and path1:
            return [], True, 'path2 not found'
        elif path1 is None and path2 is None:
            return [], True, 'both paths not found'

        city_state_target1 = ['Country'] + path1
        city_state_target2 = ['Country'] + path2

        min_len = min(len(city_state_target1), len(city_state_target2))
        if len(city_state_target1) == len(city_state_target2):
            min_len -= 1  # Ignorar último nível (freguesia)

        city_state_target_min = min(city_state_target1, city_state_target2)
        city_state_target_max = max(city_state_target1, city_state_target2)

        for i in range(min_len):
            if city_state_target_min[i] == city_state_target_max[i]:
                equal_index.append(i)

    elif (target_state1_nan and not target_state2_nan) or\
            (target_state2_nan and not target_state1_nan):
        if target_state1_nan:
            known_target = target_state2
            known_paths = all_city_paths2
            unknown_paths = all_city_paths1
        else:
            known_target = target_state1
            known_paths = all_city_paths1
            unknown_paths = all_city_paths2

        known_path = next((path for path in known_paths if known_target in path), None)  # noqa: E501
        known_path = ['Country'] + known_path
        unknown_paths = [['Country'] + path for path in unknown_paths]

        is_ambiguous = len(unknown_paths) > 1
        equal_index = []

        for path in unknown_paths:
            min_len = min(len(known_path), len(path))
            city_state_target_min = min(known_path, path)
            path_max = max(known_path, path)
            for i in range(min_len):
                if city_state_target_min[i] == path_max[i]:
                    equal_index.append(i)

    elif target_state1_nan and target_state2_nan:
        all_city_paths1 = [['Country'] + path for path in all_city_paths1]
        all_city_paths2 = [['Country'] + path for path in all_city_paths2]

        # Se houver mais do que um caminho, seja numa cidade ou noutra,
        # então é ambíguo
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
    """
    For each row in the DataFrame, find the paths from city_1 and city_2\
        to their respective target states (state_1 and state_2).
    Args:
        df (pd.DataFrame): DataFrame containing city and state information.
        data (dict): JSON data structure containing the hierarchy of cities\
            and states.
    Returns:
        pd.DataFrame: Updated DataFrame with expected levels and ambiguity\
            information.
    """
    is_ambiguous = False

    expected_levels = []
    is_ambiguous_list = []

    # for idx, row in df.iterrows()
    # However, # df.iterrows() is not efficient for large DataFrames:
    for row in df.itertuples(index=False):
        city1 = row.city_1
        target_state1 = row.state_1
        city2 = row.city_2
        target_state2 = row.state_2
        # Find all paths for city1 and city2
        all_city_paths1 = find_paths(data, city1)
        all_city_paths2 = find_paths(data, city2)

        if not all_city_paths1 or not all_city_paths2:
            # Acho que a ideia acaba por ser esta.
            # Se não é passado nenhuma cidade e é passado apenas o estado,
            #   então o maior nível o país
            # Ou se um all_city_paths é vazio, então o maior nível é o país
            expected_level = 2
            # Acho que não é ambíguo. Se só é passado o estado, então é o país
            is_ambiguous = False
            expected_levels.append(expected_level)
            is_ambiguous_list.append(1 if is_ambiguous else 0)
        else:
            equal_index, is_ambiguous, city_state_target_min =\
                compare_city_paths(target_state1, target_state2,
                                   all_city_paths1, all_city_paths2)

            if len(equal_index) > 0:
                path = city_state_target_min[:max(equal_index)+1]
                if path and path[0] == 'Country':
                    # Remove 'Country' if it's the first element. Which it is
                    path = path[1:]
                expected_level = get_admin_level(data, path)

                expected_levels.append(expected_level)
                is_ambiguous_list.append(1 if is_ambiguous else 0)
            else:  # Caso não tenha sido encontrado nenhum caminho
                expected_levels.append(city_state_target_min)
                is_ambiguous_list.append(city_state_target_min)

    df['expected_level'] = expected_levels
    df['is_ambiguous'] = is_ambiguous_list
    return df


def get_admin_level(data, path):
    """
    Get the administrative level of the last element in the path.
    Args:
        data (dict): JSON data structure containing the hierarchy of cities\
            and states.
        path (list): List of city names representing the path.
    Returns:
        int: The administrative level of the last element in the path.
    """
    node = data
    if len(path) > 0:
        for name in path:
            if 'children' in node and name in node['children']:
                node = node['children'][name]
                admin_level = node.get('admin_level')
    else:
        return 2  # path is empty [] -> Only 'Country' was present, so is 2
    return admin_level


def validate_dataframe(df_path=None, from_text=None):
    """
    Validate and load a DataFrame from a CSV or Excel file, or from a text\
        string.
    Args:
        df_path (str): Path to the CSV or Excel file.
        from_text (str): Text string containing CSV data.
    Returns:
        pd.DataFrame: Loaded DataFrame.
    Raises:
        ValueError: If neither df_path nor from_text is provided, or if the\
            file format is unsupported.
    """
    if df_path:
        if df_path.endswith('.csv'):
            df = pd.read_csv(df_path)
        elif df_path.endswith('.xlsx'):
            df = pd.read_excel(df_path)
        else:
            raise ValueError("Unsupported file format. Use .csv or .xlsx")

    elif from_text:
        df = pd.read_csv(StringIO(from_text), sep=',', header=0)
        df = df.reindex(columns=['id_1', 'id_2',
                                 'city_1', 'city_2',
                                 'state_1', 'state_2'])
    else:
        raise ValueError("No DataFrame source provided. Use df_path or\
                            from_text")

    return df


if __name__ == "__main__":
    json_file = "portugal.json"

    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    dataframe = """id_1,id_2,city_1,city_2,state_1,state_2
    1,2,valadares,valadares,viseu,porto
    1,3,valadares,valadares,viseu,
    4,5,valadares,valadares,,
    7,1,"lugar que nao existe",valadares,viseu,
    1,8,valadares,"sao pedro do sul",viseu,viseu
    1,8,valadares,"sao pedro do sul",viseu,
    10,9,valadares,"sao pedro do sul",,viseu
    12,13,,,Porto,Porto
    1,2,valadares,valadares,aveiro,porto
    15,16,ponta do sol,ponta do sol,madeira,madeira
    """
    # df = validate_dataframe(from_text=dataframe)

    df = validate_dataframe(df_path="dataframe.csv")  # or ".xlsx"

    df = city2target_paths(df, data)
    print(df)
