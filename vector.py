import os
import pandas as pd
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from config import OPENAI_API_KEY

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

db_location = "./chroma_db_langchain"
add_documents = not os.path.exists(db_location)

df = pd.read_excel("Nintendo_Cooccurrence_Matrix.xlsx", index_col=0)

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

if add_documents:
    documents = []
    ids = []

    for i, row_product in enumerate(df.index):
        for j, col_product in enumerate(df.columns):
            # Garante que só tratamos cada par uma vez (para não duplicar, por exemplo, A-B e B-A)
            if j < i:
                continue

            value = df.iloc[i, j]

            if row_product == col_product:
                document_text = f"{row_product} was sold alone {value} times"  # Não convem criar mais frases "parecidas" porque cria redundância e só aumenta o tamanho do banco de dados excusamente
            else:
                products = sorted([row_product, col_product])
                document_text = f"{products[0]} was sold together with {products[1]} {value} times"

            doc_id = f"{sorted([row_product, col_product])[0]}__{sorted([row_product, col_product])[1]}"

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


vector_store = Chroma(
    collection_name="My_data",
    persist_directory=db_location,
    embedding_function=embeddings,
)

if add_documents:
    vector_store.add_documents(documents, ids=ids)
    # vector_store.persist()

retriever = vector_store.as_retriever(search_kwargs={"k": 5})
