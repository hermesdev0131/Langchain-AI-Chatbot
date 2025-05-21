from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/qa/stream")
async def qa_stream(request: Request):
    body = await request.json()
    user_query = body.get("userMessage", "")
    logger.debug(f"qa_stream: Received streaming request for query: '{user_query}'")

    # Define a placeholder for newlines to ensure SSE compatibility
    NEWLINE_PLACEHOLDER = "__NEWLINE__"

    async def event_source():
        logger.debug(f"qa_stream: Starting event_source for query: '{user_query}'")
        processed_token_count = 0
        async for token_from_provider in request.state.provider.answer_query_stream(user_query):
            
            parts_to_send = []
            current_segment = ""
            # Split the token from provider by actual newlines,
            # then send text segments and newline placeholders as separate SSE events.
            for char in token_from_provider:
                if char == "\n":
                    if current_segment: # Send accumulated segment before the newline
                        parts_to_send.append(current_segment)
                        current_segment = ""
                    parts_to_send.append(NEWLINE_PLACEHOLDER) # Send newline placeholder
                else:
                    current_segment += char
            if current_segment: # Send any remaining segment after the loop
                parts_to_send.append(current_segment)

            for part_to_yield in parts_to_send:
                # This log can be very verbose, ensure it's DEBUG or commented out for production
                logger.debug(f"qa_stream: Server sending part to client (repr): {part_to_yield!r}")
                yield f"data: {part_to_yield}\n\n"
                processed_token_count += 1
            
        logger.debug(f"qa_stream: Finished sending parts. Total parts sent: {processed_token_count}. Sending end-of-stream.")
        yield f"data: end-of-stream\n\n"  # Sentinel for browser‑side cleanup
        logger.debug(f"qa_stream: Event_source completed for query: '{user_query}'")

    headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",  # disable nginx buffering if you use it
    }
    return StreamingResponse(event_source(), headers=headers)