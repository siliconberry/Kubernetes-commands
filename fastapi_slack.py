import os
import asyncio
from fastapi import FastAPI, Request
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
import aiohttp
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI()

# Initialize Slack app
slack_app = AsyncApp(token=os.environ["SLACK_BOT_TOKEN"])
slack_handler = AsyncSlackRequestHandler(slack_app)

# Slack event handlers
@slack_app.event("app_mention")
async def handle_app_mention(body, say):
    logger.info("Received app mention in Slack")
    event = body["event"]
    response = await send_to_chainlit(event["text"])
    await say(response)

@slack_app.event("message")
async def handle_message(body, say):
    logger.info("Received message in Slack")
    event = body["event"]
    if "channel_type" in event and event["channel_type"] == "channel":
        response = await send_to_chainlit(event["text"])
        await say(response)

async def send_to_chainlit(message):
    async with aiohttp.ClientSession() as session:
        async with session.post('http://localhost:8000/slack_message', json={'message': message}) as resp:
            return await resp.text()

# FastAPI routes
@app.post("/slack/events")
async def endpoint(req: Request):
    return await slack_handler.handle(req)

@app.get("/")
async def get():
    return {"message": "FastAPI with Slack integration is running"}

# Background tasks
@app.on_event("startup")
async def startup_event():
    # Start Slack app in Socket Mode
    handler = AsyncSocketModeHandler(slack_app, os.environ["SLACK_APP_TOKEN"])
    asyncio.create_task(handler.start_async())

# Run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
