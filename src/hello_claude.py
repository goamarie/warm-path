import anthropic
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic()

message = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=100,
    messages=[
        {"role": "user", "content": "Say hello and confirm you're ready to help find warm paths into companies."}
    ]
)

print(message.content[0].text)