import json
import pandas as pd
from itertools import combinations


def extract_city_state_pairs(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    locations = []

    for region_name, region_data in data["children"].items():
        municipalities = region_data.get("children", {})

        for municipality_name, municipality_data in municipalities.items():
            parishes = municipality_data.get("children", {})

            for parish_name in parishes:
                locations.append({
                    "city": parish_name,
                    "state": region_name
                })

    return pd.DataFrame(locations)


def generate_city_pairs(df_locations):
    # Add a unique ID for each city
    df_locations = df_locations.reset_index(drop=True)
    df_locations["id"] = df_locations.index + 1  # 1-based indexing

    # Generate all combinations of 2 cities (without repetition)
    pairs = list(combinations(df_locations.to_dict("records"), 2))

    # O "df_locations.to_dict("records")" faz com que passe de:
    # [
    #     {"id": 1, "city": "Lisboa", "state": "Lisboa"},
    #     {"id": 2, "city": "Porto", "state": "Porto"},
    #     {"id": 3, "city": "Coimbra", "state": "Coimbra"}
    # ]

    # Para isto:
    # [
    #     (
    #         {"id": 1, "city": "Lisboa", "state": "Lisboa"},
    #         {"id": 2, "city": "Porto", "state": "Porto"}
    #     ),
    #     (
    #         {"id": 1, "city": "Lisboa", "state": "Lisboa"},
    #         {"id": 3, "city": "Coimbra", "state": "Coimbra"}
    #     ),
    #     (
    #         {"id": 2, "city": "Porto", "state": "Porto"},
    #         {"id": 3, "city": "Coimbra", "state": "Coimbra"}
    #     )
    # ]

    records = []
    for a, b in pairs:
        records.append({
            "id_1": a["id"],
            "id_2": b["id"],
            "city_1": a["city"],
            "city_2": b["city"],
            "state_1": a["state"],
            "state_2": b["state"],
        })

    return pd.DataFrame(records)


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


def compute_expected_level(df):
    for index, row in df[208:209].iterrows():  # É a 10 linha apenas
    # for index, row in df.head(1).iterrows():  # Para iterar apenas a primeira linha
    # for index, row in df.iterrows():
        print(f"city_1 = {row['city_1']}, city_2 = {row['city_2']}, state_1 = {row['state_1']}, state_2 = {row['state_2']}")
        # city_1,city_2,state_1,state_2
        print(get_parents(data, f"{row['city_1']}"))
        print(get_parents(data, f"{row['city_2']}"))
        print(get_parents(data, f"{row['state_1']}"))
        print(get_parents(data, f"{row['state_2']}"))


if __name__ == "__main__":
    json_file = "portugal.json"

    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # print(get_parents(data, "ponta do sol"))
    # print(get_parents(data, "madeira"))
    df_locations = extract_city_state_pairs(json_file)
    df_pairs = generate_city_pairs(df_locations)
    compute_expected_level(df_pairs)


    # print(df_pairs.head())

    # # Save result if needed
    # df_pairs.to_csv("city_state_pairs.csv", index=False)
    # df_pairs.to_excel("city_state_pairs.xlsx", index=False)  # TODO: Corrigir depois o problema de memoria
