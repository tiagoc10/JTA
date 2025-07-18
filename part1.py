import json
from io import StringIO
import pandas as pd


class AdminTree:
    def __init__(self, data):
        self.data = data

    def find_paths(self, target_city, current_path=None, node=None):
        '''
            Required recursive search
        '''
        if node is None:
            node = self.data
        found_paths = []
        if current_path is None:
            current_path = []  # Start with an empty path if not provided
        for name, details in node.get("children", {}).items():
            new_path = current_path + [name]
            if name == target_city:
                found_paths.append(new_path)
            found_paths += self.find_paths(target_city, new_path, details)
        return found_paths

    def get_admin_level(self, path):
        """
        Traverse the JSON tree following the path, return 'admin_level' at the end of the path.
        """
        node = self.data
        if path and path[0] == 'Portugal':
            path = path[1:]
        if len(path) > 0:
            for name in path:
                if 'children' in node and name in node['children']:
                    node = node['children'][name]
                    admin_level = node.get('admin_level')
        else:
            return 2  # Only 'Portugal'
        return admin_level


class CityPathComparator:
    def __init__(self, admin_tree):
        self.admin_tree = admin_tree

    def compare_city_paths(self, target_state1, target_state2,
                          all_city_paths1, all_city_paths2):
        equal_index = []
        is_ambiguous = False
        city_state_target_min = None
        if not pd.isna(target_state1) and not pd.isna(target_state2):
            is_ambiguous = False
            paths1 = [path for path in all_city_paths1 if target_state1 in path]
            paths2 = [path for path in all_city_paths2 if target_state2 in path]
            if len(paths1) > 1:
                paths1 = [max(paths1, key=len)]
                is_ambiguous = True
            if len(paths2) > 1:
                paths2 = [max(paths2, key=len)]
                is_ambiguous = True
            path1 = next((path for path in paths1 if target_state1 in path), None)
            path2 = next((path for path in paths2 if target_state2 in path), None)
            if path1 is None and path2:
                return None, None, 'path1 not found'
            elif path2 is None and path1:
                return None, None, 'path2 not found'
            elif path1 is None and path2 is None:
                return None, None, 'both paths not found'
            if path1 is not None:
                city_state_target1 = ['Portugal'] + path1
            else:
                city_state_target1 = None
            if path2 is not None:
                city_state_target2 = ['Portugal'] + path2
            else:
                city_state_target2 = None
            if city_state_target1 is not None and city_state_target2 is not None:
                min_len = min(len(city_state_target1), len(city_state_target2))
                if len(city_state_target1) == len(city_state_target2):
                    min_len -= 1
                city_state_target_min = min(city_state_target1, city_state_target2)
                city_state_target_max = max(city_state_target1, city_state_target2)
                for i in range(min_len):
                    if city_state_target_min[i] == city_state_target_max[i]:
                        equal_index.append(i)
        elif (pd.isna(target_state1) and not pd.isna(target_state2)) or \
             (pd.isna(target_state2) and not pd.isna(target_state1)):
            if pd.isna(target_state1):
                known_target = target_state2
                known_paths = all_city_paths2
                unknown_paths = all_city_paths1
            else:
                known_target = target_state1
                known_paths = all_city_paths1
                unknown_paths = all_city_paths2
            known_path = next((path for path in known_paths if known_target in path), None)
            known_path = (
                ['Portugal'] + known_path if known_path is not None else None
            )
            unknown_paths = [['Portugal'] + path for path in unknown_paths]
            is_ambiguous = len(unknown_paths) > 1
            equal_index = []
            for path in unknown_paths:
                if known_path is None:
                    continue
                min_len = min(len(known_path), len(path))
                city_state_target_min = min(known_path, path)
                path_max = max(known_path, path)
                for i in range(min_len):
                    if city_state_target_min[i] == path_max[i]:
                        equal_index.append(i)
        elif pd.isna(target_state1) and pd.isna(target_state2):
            all_city_paths1 = [['Portugal'] + path for path in all_city_paths1]
            all_city_paths2 = [['Portugal'] + path for path in all_city_paths2]
            is_ambiguous = (
                len(all_city_paths1) > 1 or len(all_city_paths2) > 1
            )
            for path1 in all_city_paths1:
                for path2 in all_city_paths2:
                    min_len = min(len(path1), len(path2))
                    city_state_target_min = min(path1, path2)
                    city_state_target_max = max(path1, path2)
                    for i in range(min_len):
                        if city_state_target_min[i] == city_state_target_max[i]:
                            equal_index.append(i)
        return equal_index, is_ambiguous, city_state_target_min


class CityPathProcessor:
    def __init__(self, admin_tree):
        self.admin_tree = admin_tree
        self.comparator = CityPathComparator(admin_tree)

    def city2target_paths(self, df):
        is_ambiguous = False
        for idx, row in df.iterrows():
            city1 = row['city_1']
            target_state1 = row['state_1']
            city2 = row['city_2']
            target_state2 = row['state_2']
            all_city_paths1 = self.admin_tree.find_paths(city1)
            all_city_paths2 = self.admin_tree.find_paths(city2)
            if not all_city_paths1 or not all_city_paths2:
                expected_level = 2
                is_ambiguous = False
                df.loc[idx, 'expected_level'] = expected_level
                df.loc[idx, 'is_ambiguous'] = 1 if is_ambiguous else 0
            else:
                (
                    equal_index, is_ambiguous, city_state_target_min
                ) = self.comparator.compare_city_paths(
                    target_state1, target_state2,
                    all_city_paths1, all_city_paths2
                )
                if equal_index is not None and is_ambiguous is not None:
                    expected_level = self.admin_tree.get_admin_level(
                        city_state_target_min[:max(equal_index)+1]
                    )
                    df.loc[idx, 'expected_level'] = expected_level
                    df.loc[idx, 'is_ambiguous'] = 1 if is_ambiguous else 0
                else:
                    df.loc[idx, 'expected_level'] = city_state_target_min
                    df.loc[idx, 'is_ambiguous'] = city_state_target_min
        def try_int(val):
            try:
                if pd.notna(val) and str(val).strip().isdigit():
                    return int(val)
                if isinstance(val, float) and val.is_integer():
                    return int(val)
            except Exception:
                pass
            return val
        df['expected_level'] = df['expected_level'].apply(try_int)
        df['is_ambiguous'] = df['is_ambiguous'].apply(try_int)
        return df


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
1;2;valadares;valadares;aveiro;porto
15;16;ponta do sol;ponta do sol;madeira;madeira
"""
    df = pd.read_csv(StringIO(dataframe), sep=';', header=0)
    df = df.reindex(
        columns=['id_1', 'id_2', 'city_1', 'city_2', 'state_1', 'state_2']
    )
    admin_tree = AdminTree(data)
    processor = CityPathProcessor(admin_tree)
    df = processor.city2target_paths(df)
    print(df)
