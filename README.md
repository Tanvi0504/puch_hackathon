My Awesome To-Do Bot: A WhatsApp Task Manager
A voice-powered to-do list bot built with Puch AI to help users manage their daily tasks directly from WhatsApp.

#BuildWithPuch      

🚀 Features
Multilingual Task Management: Add, show, complete, and delete tasks for "today," "this week," or "this month" using natural language.

Voice-First Interaction: The bot can interpret voice messages to perform tasks, making it accessible for a wider audience.

Persistent Storage: All tasks are saved to a local SQLite database, ensuring they are not lost when the server restarts.

Secure & Scalable: The bot is built on the FastMCP framework, ensuring a secure and efficient connection to Puch AI.

🛠️ How to Run Locally
Follow these steps to set up and run the bot on your local machine.

Prerequisites

Python 3.10+

uv or pip (Python package manager)

ngrok (for creating a public URL)

Your Puch AI AUTH_TOKEN and MY_NUMBER

Setup

Clone the repository:

Bash
git clone https://github.com/Tanvi0504/puch_hackathon.git
cd puch_hackathon/mcp-starter
Set up the environment:

Bash
python3 -m venv .venv
source .venv/bin/activate
uv sync # or pip install -r requirements.txt
Configure .env file:
Create a file named .env in the mcp-starter directory with your secret keys.

AUTH_TOKEN="<your_secret_auth_token>"
MY_NUMBER="<your_phone_number>"
USE_MCP=true
Run the server:

Bash
python3 mcp_starter.py
Start ngrok in a new terminal:

Bash
ngrok http 8086
🔗 How to Use
Once your server is running and connected via ngrok, use the following commands in your WhatsApp chat with Puch AI to interact with the bot.

Connect to the server:
/mcp connect <your_ngrok_url>/mcp <your_auth_token>

Add a task:
"Add buy groceries to today"

List tasks:
"Show me my tasks for today"

Complete a task:
"Complete buy groceries"

Delete a task:
"Delete buy groceries"

📂 File Structure
mcp_starter.py: The core MCP server file where all custom tools (add_task, list_tasks, etc.) are defined.

whatsappbot/db.py: Handles all database operations using SQLite.

whatsappbot/nlu.py: Contains the logic for parsing user messages and identifying intents.

whatsappbot/mcp_client.py: The client that makes API calls to our MCP server.
