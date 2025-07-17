# Vector search is a database. That is hosted locally, called ChromaDB.
# This allows to really look up relevant information that we can than pass to our model.

from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
import os
import pandas as pd
from config import OPENAI_API_KEY
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

df = pd.read_excel("Nintendo_Cooccurrence_Matrix.xlsx")  # Atenção que pode ter varias folhas

# O embedding são usados para converter texto em vetores numéricos que capturam o significado semântico do texto.
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")  # Existe o modelo "text-embedding-3-small" também mas é menos preciso embora mais rápido

db_location = "./chroma_db_langchain"  # Local onde a base de dados vai ser guardada

add_documents = not os.path.exists(db_location)  # Se a base de dados não existir, adicionar documentos

if add_documents:
    documents = []
    ids = []
    for i, row in df.iterrows():
        document_text = (
            str(row["Nintendo Switch"]) + " " + str(row["Zelda: Breath of the Wild"]) + " " +
            str(row["Zelda: Tears of the Kingdom"]) + " " + str(row["Super Mario Odyssey"]) + " " +
            str(row["Mario Kart 8 Deluxe"]) + " " + str(row["Mario Party Superstars"]) + " " +
            str(row["Sonic Generations"]) + " " + str(row["Sonic Mania"]) + " " +
            str(row["Animal Crossing: New Horizons"]) + " " + str(row["Splatoon 3"]) + " " +
            str(row["Pikmin 4"]) + " " + str(row["Nintendo Switch Pro Controller"]) + " " +
            str(row["Joy-Con Controllers (Pair)"]) + " " + str(row["Nintendo Switch Dock Set"]) + " " +
            str(row["Nintendo Switch Carrying Case"]) + " " + str(row["Nintendo Switch Screen Protector"])
            )

        document = Document(
            page_content=document_text,  # The actual text content of the document
            metadata={"data": document_text},  # Metadata is used to store additional information about the document
            id=str(i)  # Unique identifier for the document
        )
        ids.append(str(i))  # Store the id of the document
        documents.append(document)  # Add the document to the list

vector_store = Chroma(
    collection_name='My_data',
    persist_directory=db_location,  # Directory where the database is stored
    embedding_function=embeddings,  # Function to convert text to vectors
)

if add_documents:
    vector_store.add_documents(documents, ids=ids)  # Add the documents to the vector store
    # vector_store.persist()  # Persist the changes to the database

retriever = vector_store.as_retriever(
    search_kwargs={"k": 5},  # It is gonna look for the 5 most relevant documents  # TODO: Perceber qual o valor ideal para k
)
