import aiohttp
from typing import Optional
from asyncio import TimeoutError
from os import getenv

BASE_API_URL = getenv("LANGFLOW_BASE_API_URL")
FLOW_ID = getenv("FLOW_ID")

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

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(api_url, json=payload, headers=headers, timeout=10) as response:
                response_json = await response.json()
                
                return (
                    response_json.get("outputs", [{}])[0]
                    .get("outputs", [{}])[0]
                    .get("outputs", {})
                    .get("message", {})
                    .get("message", {})
                    .get("text", "No response text found")
                )
        except TimeoutError:
            return {"error": "API request timed out"}
        except aiohttp.ClientError as e:
            return {"error": f"API request failed: {str(e)}"}
