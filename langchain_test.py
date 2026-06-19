from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv

load_dotenv()

model = ChatAnthropic(model="claude-sonnet-4-6")

response = model.invoke(
    "Say hello and tell me one fun fact about community gardens.")

print(response.content)
