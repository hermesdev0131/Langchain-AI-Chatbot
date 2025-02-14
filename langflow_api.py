import aiohttp
from typing import Optional

BASE_API_URL = "https://langflow-te0k.onrender.com"
FLOW_ID = "62283816-fdec-48d4-a1f2-5205cbbaf3ee"

async def run_flow(
    message: str,
    output_type: str = "chat",
    input_type: str = "chat",
    tweaks: Optional[dict] = None,
    api_key: Optional[str] = None
) -> dict:
    """
    Run a flow with a given message and optional tweaks.

    :param message: The message to send to the flow
    :param output_type: The type of output expected
    :param input_type: The type of input provided
    :param tweaks: Optional tweaks to customize the flow
    :param api_key: Optional API key for authentication
    :return: The response text from the flow
    """
    api_url = f"{BASE_API_URL}/api/v1/run/{FLOW_ID}"

    payload = {
        "input_value": message,
        "output_type": output_type,
        "input_type": input_type,
    }
    headers = {}
    if tweaks:
        payload["tweaks"] = tweaks
    if api_key:
        headers["x-api-key"] = api_key

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=payload, headers=headers) as response:
                response_json = await response.json()
                print("API Response: ", response_json)
                return response_json["outputs"][0]["outputs"][0]["outputs"]["message"]["message"]["text"]
    except aiohttp.ClientError as e:
        return {"error": str(e)}
