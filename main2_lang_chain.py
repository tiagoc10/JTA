from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os
from vector import retriever

from config import OPENAI_API_KEY
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

model = ChatOpenAI(model_name="gpt-3.5-turbo",
                   temperature=0.3,        # Menor temperature → respostas mais focadas
                #    max_tokens=150          # Limite de tokens na resposta
                   )

# No template especificamos o que queremos de facto que o chatbot faça
template = """
You are an expert on videogames, their sales history, and gaming consoles.
You will be provided with a list of videogames along with their sales history and reviews.
Answer the user's question strictly based on this information.
Your language should be clear and concise, avoiding unnecessary details.
You need to answer in same language as the question, so if the question is in Portuguese, you should answer in Portuguese.
If the question is in English, you should answer in English.

Guidelines:
- If the question is unrelated to videogame sales, consoles, or reviews, respond politely that you don't know.
- If the question is ambiguous or unclear, ask for clarification politely.
- If the user asks for opinions or subjective judgments, say you cannot proivde opinions because you are an AI.
- If the question asks about information not in the data, respond politely that you don't have that information.
- For greetings, respond politely.
- For farewells, respond politely.
- For questions outside your expertise (e.g., hardware details), respond politely with a referral to other sources.

Here are some relevant reviews: {reviews}

Here is the question to answer: {question}
"""

prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

print("Chatbot online! Press 'q' or 'quit' or 'exit' to exit")
while True:
    print("\n---------------------------\n")
    question = input("User: ")
    print("\n")
    if question.lower() in ["q", "quit", "exit"]:
        break
    reviews = retriever.invoke(question)  # Retrieve relevant documents based on the question
    result = chain.invoke({"reviews": reviews, "question": question})
    print(result.content)  # Print the answer from the model
