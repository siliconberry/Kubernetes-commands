import chainlit as cl
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/slack_message")
async def receive_slack_message(request: Request):
    data = await request.json()
    message = data['message']
    response = await process_message(message)
    return response

async def process_message(message):
    # This is where you'd implement your Chainlit logic
    return f"Processed: {message}"

@cl.on_chat_start
async def start():
    await cl.Message(content="Chainlit is ready!").send()

@cl.on_message
async def main(message: cl.Message):
    response = await process_message(message.content)
    await cl.Message(content=response).send()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8089)
