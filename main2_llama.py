from llama_index.core import VectorStoreIndex, Settings
from llama_index.core.schema import Document
from llama_index.llms.openai import OpenAI
from llama_index.core.chat_engine import CondenseQuestionChatEngine

import pandas as pd
import os
import json

from config import OPENAI_API_KEY
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

################ Excel ################
# df = pd.read_excel("Nintendo_Cooccurrence_Matrix.xlsx")
# document = Document(text=df.to_string())
################ Excel ################

################ JSON ################
with open("dataset.json", "r", encoding="utf-8") as f:
    data = json.load(f)

json_text = json.dumps(data, indent=2)
# Create the document
document = Document(text=json_text)
################ JSON ################

# Define the LLM
llm = OpenAI(model="gpt-3.5-turbo")

# Set the LLM globally in LlamaIndex settings
Settings.llm = llm

# Index with the JSON document
index = VectorStoreIndex.from_documents([document])

# Create the chat engine with memory
chat_engine = CondenseQuestionChatEngine.from_defaults(
    query_engine=index.as_query_engine()
)

print("✅ Chatbot is running. Type 'exit' to quit.\n")
while True:
    question = input("User: ")
    if question.lower() in ["exit", "quit", "goodbye"]:
        print("Goodbye!")
        break
    response = chat_engine.chat(question)
    if len(response.response) < 20 or "don't know" in response.response.lower():
        # fallback: call GPT directly (without index context)
        fallback_response = llm.chat(question)
        print(f"Bot (GPT fallback): {fallback_response.response}\n")
    else:
        print(f"Bot: {response.response}\n")
