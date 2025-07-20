from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os
from vector import create_llm

from config import OPENAI_API_KEY
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY


def chatbot(xlsx_file, json_file):
    """
    Start a chatbot that uses the LLM to answer questions based on the\
        provided xlsx and json files.
    Args:
        xlsx_file (str): Path to the xlsx file containing co-occurrence data.
        json_file (str): Path to the json file containing product data.
    Raises:
        ValueError: If the xlsx or json file paths are not provided.
    Returns:
        None
    This function initializes a chatbot that listens for user input and\
        responds based on the provided data.
    It uses the LLM to process the input and generate responses based on the\
        context of the provided xlsx and json files.
    The chatbot will continue to run until the user decides to exit by typing\
        'q', 'quit', or 'exit'.
    """
    retriever = create_llm(xlsx_file, json_file)
    model = ChatOpenAI(model_name="gpt-3.5-turbo",
                       temperature=0.3,
                       )  # Lower temperature value → more focused responses

    template = """
    You are an expert on videogames, their sales history, and gaming consoles.
    You will be provided with a list of videogames along with their sales\
        history and reviews.
    Answer the user's question strictly based on this information.
    Your language should be clear and concise, avoiding unnecessary details.
    You need to answer in same language as the question, so if the question is\
        in Portuguese, you should answer in Portuguese.
    If the question is in English, you should answer in English.

    Guidelines:
    - If the question is unrelated to videogame sales, consoles, or reviews,\
        respond politely that you don't know.
    - If the question is ambiguous or unclear, ask for clarification politely.
    - If the user asks for opinions or subjective judgments, say you cannot\
        provide opinions because you are an AI.
    - If the question asks about information not in the data, respond politely\
        that you don't have that information.
    - For greetings, respond politely.
    - For farewells, respond politely.
    - For questions outside your expertise, respond politely that you dont\
        have the related information.

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
            print("Exiting the chatbot. Goodbye!")
            break
        # Retrieve relevant documents based on the question
        reviews = retriever.invoke(question)
        result = chain.invoke({"reviews": reviews, "question": question})
        print(f"Bot: {result.content}")  # Print the answer from the model


if __name__ == "__main__":
    xlsx_file = "Nintendo_Cooccurrence_Matrix.xlsx"
    json_file = "dataset.json"
    chatbot(xlsx_file, json_file)
