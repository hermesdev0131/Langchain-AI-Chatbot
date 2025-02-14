import aiofiles
from quart import Quart, request, jsonify, Response
import os
from dotenv import load_dotenv
from langflow_api import run_flow

load_dotenv()
RENDER_LANGFLOW_API_KEY = os.getenv("RENDER_LANGFLOW_API_KEY")

app = Quart(__name__, static_folder='static')

# Serve the static index.html
@app.route('/', methods=['GET'])
async def serve_index():
    file_path = os.path.join(app.static_folder, "index.html")
    try:
        async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
            content = await f.read()
        return Response(content, mimetype='text/html')
    except FileNotFoundError:
        return Response("index.html not found", status=404)

# Handle POST requests from the front-end
@app.route('/', methods=['POST'])
async def handle_post():
    data = await request.get_json()
    user_message = data.get('userMessage', 'No message provided')

    response = await run_flow(user_message, api_key=RENDER_LANGFLOW_API_KEY)

    return jsonify({"response": response})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
