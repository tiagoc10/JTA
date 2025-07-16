from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, Tool, AgentType
from langchain.schema import HumanMessage
import os

from config import OPENAI_API_KEY
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)

def gpt_fallback_tool(query: str) -> str:
    response = llm.invoke([HumanMessage(content=query)])
    return response.content

tools = [
    Tool(
        name="GPT Fallback",
        func=gpt_fallback_tool,
        description="Use para perguntas gerais."
    )
]

agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=False)

print("Chatbot online. Type 'exit' to exit :)")

while True:
    question = input("User: ")
    if question.lower() == "exit":
        break
    answer = agent.invoke(question)
    print("Bot:", answer["output"])
