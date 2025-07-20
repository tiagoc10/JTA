import json
from io import StringIO
import pandas as pd


class CityHierarchy:
    def __init__(self, data):
        self.data = data

    def find_paths(self, target_city, current_path=None):
        """
        Recursively find all paths in the JSON structure that lead to the\
            target city.
        Args:
            target_city (str): The name of the city to find paths for.
            current_path (list): The current path being explored.
        Returns:
            list: A list of paths (as lists of city names) that lead to the\
                  target city.
        """
        found_paths = []
        if current_path is None:
            current_path = []

        for name, details in self.data.get("children", {}).items():
            current_path.append(name)
            if name == target_city:
                found_paths.append(list(current_path))
            # Use a new CityHierarchy for recursion to keep 'data' context
            found_paths.extend(
                CityHierarchy(details).find_paths(target_city, current_path)
            )
            current_path.pop()

        return found_paths

    def get_admin_level(self, path):
        """
        Get the administrative level of the last element in the path.
        Args:
            path (list): A list of city names representing the path.
        Returns:
            int: The administrative level of the last city in the path.
        If the path is empty, returns 2 (indicating only 'Country' was present)
        """
        node = self.data
        if len(path) > 0:
            for name in path:
                if 'children' in node and name in node['children']:
                    node = node['children'][name]
                    admin_level = node.get('admin_level')
        else:
            return 2  # path is empty [] -> Only 'Country' was present, so is 2
        return admin_level


class CityPathAnalyzer:
    def __init__(self, city_hierarchy):
        self.city_hierarchy = city_hierarchy

    def compare_city_paths(self, target_state1, target_state2,
                           all_city_paths1, all_city_paths2):
        """
        Compare paths of two cities to determine the common path to their
        respective states.
        Args:
            target_state1 (str): The target state for the first city.
            target_state2 (str): The target state for the second city.
            all_city_paths1 (list): All paths for the first city.
            all_city_paths2 (list): All paths for the second city.
        Returns:
            - equal_index (list): Indices where the paths are equal.
            - is_ambiguous (bool): Whether the paths are ambiguous.
            - city_state_target_min (list): The minimum path to the target
                state.
        """
        equal_index = []
        is_ambiguous = False
        city_state_target_min = []

        target_state1_nan = pd.isna(target_state1)
        target_state2_nan = pd.isna(target_state2)

        if not target_state1_nan and not target_state2_nan:
            is_ambiguous = False

            # All paths with the target_state1
            paths1 = [path for path in all_city_paths1 if target_state1 in path]  # noqa: E501
            # All paths with the target_state2
            paths2 = [path for path in all_city_paths2 if target_state2 in path]  # noqa: E501

            print(f"Paths1: {paths1}")
            print(f"Paths2: {paths2}")
            if paths1 == paths2 and len(paths1) == 1 and len(paths2) == 1:
                # If the paths are equal and only one path exists.
                # For example: "aveleda-aveleda-lousada-lousada"
                equal_index.append(len(paths1[0])-1)
                return equal_index, False, paths1[0]

            if len(paths1) > 1:  # For example: "ponta do sol-madeira"
                paths1 = [max(paths1, key=len)]  # Get the longest path
                is_ambiguous = True
            if len(paths2) > 1:
                paths2 = [max(paths2, key=len)]  # Get the longest path
                is_ambiguous = True

            path1 = paths1[0] if paths1 else None
            path2 = paths2[0] if paths2 else None

            if path1 is None and path2:
                return [], True, 'path1 not found'
            elif path2 is None and path1:
                return [], True, 'path2 not found'
            elif path1 is None and path2 is None:
                return [], True, 'both paths not found'

            if path1 is not None:
                city_state_target1 = ['Country'] + path1
            else:
                city_state_target1 = []
            if path2 is not None:
                city_state_target2 = ['Country'] + path2
            else:
                city_state_target2 = []

            min_len = min(len(city_state_target1), len(city_state_target2))

            if city_state_target1 == city_state_target2:
                # If both paths are equal, return the path.
                # Presents more than one path, but they one of them is equal
                #   to the other.
                equal_index.append(len(city_state_target1)-1)
                return equal_index, True, city_state_target1
            elif city_state_target1 != city_state_target2\
                    and city_state_target1[0] == city_state_target2[0]\
                    and city_state_target1[-1] == city_state_target2[-1]:
                min_len -= 1  # Exclude the last element, which is the city

            city_state_target_min = min(city_state_target1, city_state_target2)
            city_state_target_max = max(city_state_target1, city_state_target2)

            for i in range(min_len):
                if city_state_target_min[i] == city_state_target_max[i]:
                    equal_index.append(i)

        elif (target_state1_nan and not target_state2_nan) or \
                (target_state2_nan and not target_state1_nan):
            if target_state1_nan:
                known_target = target_state2
                known_paths = all_city_paths2
                unknown_paths = all_city_paths1
            else:
                known_target = target_state1
                known_paths = all_city_paths1
                unknown_paths = all_city_paths2

            known_path = next((path for path in known_paths
                               if known_target in path), None)
            if known_path is not None:
                known_path = ['Country'] + known_path
            else:
                known_path = []
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

            # If there is more than one path, whether in one city or another,
            # then it is considered ambiguous.
            is_ambiguous = len(all_city_paths1) > 1 or len(all_city_paths2) > 1
            for path1 in all_city_paths1:
                for path2 in all_city_paths2:
                    min_len = min(len(path1), len(path2))
                    city_state_target_min = min(path1, path2)
                    city_state_target_max = max(path1, path2)
                    for i in range(min_len):
                        if city_state_target_min[i] == city_state_target_max[i]:  # noqa: E501
                            equal_index.append(i)

        return equal_index, is_ambiguous, city_state_target_min

    def city2target_paths(self, df):
        """
        For each row in the DataFrame, find the paths from city_1 and city_2
        to their respective target states (state_1 and state_2).
        Args:
            df (pd.DataFrame): DataFrame containing city and state information.
            data (dict): JSON data structure containing the hierarchy of\
                cities and states.
        Returns:
            pd.DataFrame: Updated DataFrame with expected levels and\
                ambiguity information.
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
            all_city_paths1 = self.city_hierarchy.find_paths(city1)
            all_city_paths2 = self.city_hierarchy.find_paths(city2)

            if not all_city_paths1 or not all_city_paths2:
                # If no city is provided and only the state is given,
                #   then the highest level is the country.
                # Or if one of the all_city_paths is empty, then the highest
                #   level is also the country.
                expected_level = 2
                # If only the state is given, then the highest level is the
                #   country (2).
                is_ambiguous = False
                expected_levels.append(expected_level)
                is_ambiguous_list.append(1 if is_ambiguous else 0)
            else:
                equal_index, is_ambiguous, city_state_target_min = \
                    self.compare_city_paths(
                        target_state1, target_state2,
                        all_city_paths1, all_city_paths2)

                if len(equal_index) > 0:
                    path = city_state_target_min[:max(equal_index)+1]
                    if path and path[0] == 'Country':
                        # Remove 'Country' if it is the first element.
                        path = path[1:]
                    expected_level = self.city_hierarchy.get_admin_level(path)
                    expected_levels.append(expected_level)
                    is_ambiguous_list.append(1 if is_ambiguous else 0)
                else:  # If no path is found
                    expected_levels.append(city_state_target_min)
                    is_ambiguous_list.append(city_state_target_min)

        df['expected_level'] = expected_levels
        df['is_ambiguous'] = is_ambiguous_list
        return df


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
        raise ValueError(
            "No DataFrame source provided. Use df_path or from_text"
        )

    return df


if __name__ == "__main__":
    json_file = "portugal.json"

    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    dataframe = (
        "id_1,id_2,city_1,city_2,state_1,state_2\n"
        "1,2,valadares,valadares,viseu,porto\n"
        "1,3,valadares,valadares,viseu,\n"
        "4,5,valadares,valadares,,\n"
        "7,1,\"lugar que nao existe\",valadares,viseu,\n"
        "1,8,valadares,\"sao pedro do sul\",viseu,viseu\n"
        "1,8,valadares,\"sao pedro do sul\",viseu,\n"
        "10,9,valadares,\"sao pedro do sul\",,viseu\n"
        "12,13,,,Porto,Porto\n"
        "1,2,valadares,valadares,aveiro,porto\n"
        "15,16,aveleda,aveleda,lousada,porto\n"
    )

    # df = validate_dataframe(from_text=dataframe)

    df = validate_dataframe(df_path="dataframe.csv")  # or ".xlsx"

    city_hierarchy = CityHierarchy(data)
    analyzer = CityPathAnalyzer(city_hierarchy)
    df = analyzer.city2target_paths(df)
    print(df)
