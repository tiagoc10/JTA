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
You are an expert in answering questions about videogames

Here are some relevant reviews: {reviews}

Here is the question to answer: {question}
"""

prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

print("Chatbot online! Press 'q' or 'quit' or 'exit' to exit")
while True:
    print("\n\n---------------------------")
    question = input("User: ")
    print("\n")
    if question.lower() in ["q", "quit", "exit"]:
        break
    reviews = retriever.invoke(question)  # Retrieve relevant documents based on the question
    result = chain.invoke({"reviews": reviews, "question": question})
    print(result.content)  # Print the answer from the model
