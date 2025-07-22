import os
import json
import pandas as pd
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from config import OPENAI_API_KEY

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY


def create_llm(xlsx_file, json_file):
    """
    Create a retriever for the LLM using the provided xlsx and json files.
    Args:
        xlsx_file (str): Path to the xlsx file containing co-occurrence data.
        json_file (str): Path to the json file containing product data.
    Returns:
        retriever: A retriever object that can be used to query the LLM.
    Raises:
        ValueError: If the xlsx or json file paths are not provided.
    """
    if not xlsx_file:
        raise ValueError("XLSX file path must be provided.")
    if not json_file:
        raise ValueError("JSON file path must be provided.")

    db_location = "./chroma_db_langchain"
    add_documents = not os.path.exists(db_location)

    df = pd.read_excel(xlsx_file, index_col=0)

    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

    documents = []
    ids = []

    # Xlsx data processing
    if add_documents:
        for i, row_product in enumerate(df.index):
            for j, col_product in enumerate(df.columns):
                if j < i:
                    continue

                value = df.iloc[i, j]
                if row_product == col_product:
                    document_text = f"{row_product} was sold alone {value} times"  # noqa: E501
                else:
                    products = sorted([row_product, col_product])
                    document_text = f"{products[0]} was sold together with {products[1]} {value} times"  # noqa: E501

                doc_id = f"{sorted([row_product, col_product])[0]}__{sorted([row_product, col_product])[1]}"  # noqa: E501
                document = Document(
                    page_content=document_text,
                    metadata={
                        "product_a": row_product,
                        "product_b": col_product,
                        "Number of sales": int(value)
                    },
                    id=doc_id
                )
                documents.append(document)
                ids.append(doc_id)

    # JSON data processing
    if add_documents:
        with open(json_file, "r", encoding="utf-8") as f:
            product_data = json.load(f)

        for category, products in product_data.items():
            for product in products:
                name = product.get("name")
                times_sold = product.get("times_sold", 0)

                description_parts = []

                if category == "Console":
                    description_parts.append(f"Console {name} was sold\
                                             {times_sold} times.")
                    for store in ["Store A", "Store B", "Store C"]:
                        if store in product and product[store] is not None:
                            description_parts.append(f"{store} sell {name} console")  # noqa: E501
                            description_parts.append(f"Console {name} was sold in {store} {product[store]} times.")  # noqa: E501
                        elif store in product and product[store] is None:
                            description_parts.append(f"{store} did not sell\
                                                     {name} console.")

                elif category == "Games":
                    description_parts.append(f"Game {name} was sold\
                                             {times_sold} times.")
                    for store in ["Store A", "Store B", "Store C"]:
                        if store in product and product[store] is not None:
                            description_parts.append(f"{store} sell {name} game.")  # noqa: E501
                            description_parts.append(f"Game {name} was sold in {store} {product[store]} times.")  # noqa: E501
                        elif store in product and product[store] is None:
                            description_parts.append(f"{store} did not sell\
                                                     {name} game.")
                    if "release_date" in product:
                        description_parts.append(f"Game {name} was released in\
                                                 {product['release_date']}.")
                    if "type" in product:
                        description_parts.append(f"Game {name} is\
                                                 {product['type']} type.")
                    if "franchise" in product:
                        description_parts.append(f"{name} game belongs to franchise {product['franchise']}.")  # noqa: E501
                    if "min_age" in product:
                        description_parts.append(f"The minimum age required to play {name} is {product['min_age']} years old.")  # noqa: E501

                elif category == "Accessories":
                    description_parts.append(f"Accessory {name} was sold\
                                             {times_sold} times.")
                    for store in ["Store A", "Store B", "Store C"]:
                        if store in product and product[store] is not None:
                            description_parts.append(f"{store} sell {name} acessory.")  # noqa: E501
                            description_parts.append(f"Accessory {name} was sold in {store} {product[store]} times.")  # noqa: E501
                        elif store in product and product[store] is None:
                            description_parts.append(f"{store} did not sell\
                                                     {name} acessory.")
                    if "category" in product:
                        description_parts.append(f"Accessory {name} is a\
                                                 {product['category']}.")

                description = " ".join(description_parts)

                doc_id = f"{category}_{name.replace(' ', '_')}"
                document = Document(
                    page_content=description,
                    metadata={
                        "name": name,
                        "category": category,
                        "times_sold": times_sold
                    },
                    id=doc_id
                )
                documents.append(document)
                ids.append(doc_id)

    vector_store = Chroma(
        collection_name="My_data",
        persist_directory=db_location,
        embedding_function=embeddings,
    )

    if add_documents:
        vector_store.add_documents(documents, ids=ids)

    retriever = vector_store.as_retriever(search_kwargs={"k": 5})

    return retriever


if __name__ == "__main__":
    xlsx_file = "Nintendo_Cooccurrence_Matrix.xlsx"
    json_file = "dataset.json"
    retriever = create_llm(xlsx_file, json_file)
