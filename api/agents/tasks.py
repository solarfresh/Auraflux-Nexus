import json
import logging
from datetime import datetime

from asgiref.sync import async_to_sync
from auraflux_core.core.schemas.messages import Message
from core.celery_app import celery_app
from django.utils import timezone
from messaging.constants import (InitiationEAStreamCompleted,
                                 InitiationEAStreamRequest, PersistChatEntry,
                                 TopicRefinementAgentRequest)
from messaging.tasks import publish_event
from realtime.utils import send_ws_notification

from .models import AgentRoleConfig
from .utils import compose_prompt, get_agent_instance

logger = logging.getLogger(__name__)


@celery_app.task(name=TopicRefinementAgentRequest.name, ignore_result=True)
def handle_topic_refinement_agent_request(event_type: str, payload: dict):
    """
    Consumer task for TOPIC_REFINEMENT_AGENT_REQUEST.

    1. Executes the Topic Refinement Agent (TR Agent) to get structured JSON output.
    2. Publishes TOPIC_STABILITY_UPDATED event for persisting structured data (Sidebar update).
    3. Publishes a new event to trigger the Incremental Summarizer Agent.
    """
    task_id = handle_topic_refinement_agent_request.request.id

    # Extract necessary fields for TR Agent (Structured output focused)
    session_id = payload.get('session_id')
    agent_role_name = payload.get('tr_agent_role_name')
    # Context required for TR Agent: full prompt template data, including history, summary, etc.
    tr_agent_input_data = payload.get('tr_agent_input_data', {})
    user_id = payload.get('user_id') # Required for error notifications if needed

    if not all([session_id, agent_role_name, tr_agent_input_data]):
        logger.error("Task %s: Missing critical fields (session_id, role, input_data). Aborting.", task_id)
        return

    if agent_role_name is None:
        logger.error("Task %s: Missing Explorer agent role name. Aborting.", task_id)
        return

    logger.info("Task %s: Starting TR Agent execution for session %s.", task_id, session_id)

    agent, role_config = get_agent_instance(AgentRoleConfig, agent_role_name)
    prompt_text = compose_prompt(tr_agent_input_data, role_config.prompt_template, role_config.template_variables)

    try:
        # TR Agent call uses pre-rendered prompt (tr_agent_input_data is the full prompt text)
        message = async_to_sync(agent.generate)(
            messages=[Message(role="user", content=prompt_text, name='User')]
        )

        # Parse the JSON output from the response text
        structured_output_json = json.loads(message.content.replace('```json', '').replace('```', '').strip())

        logger.info("Task %s: TR Agent returned structured data. Score: %s",
                    task_id, structured_output_json.get('new_stability_score'))

    except Exception as e:
        logger.critical("Task %s: TR Agent execution failed for session %s: %s", task_id, session_id, str(e))
        # Handle error case (e.g., notify user or set a fallback state)
        return

    # Publish event to update the sidebar/DB (Topic Stability Data)
    # publish_event.delay(
    #     event_type=TopicStabilityUpdated.name,
    #     payload={
    #         "session_id": session_id,
    #         "structured_data": structured_output_json
    #     },
    #     queue=TopicStabilityUpdated.queue
    # )

    # Publish event to trigger the Incremental Summarizer Agent
    # publish_event.delay(
    #     event_type=IncrementalSummarizerRequest.name,
    #     payload={
    #         "session_id": session_id,
    #         "sum_agent_role_name": SUM_AGENT_ROLE_NAME, # Assumes a constant defined elsewhere
    #         # Include necessary data for summarization context, e.g., the last few raw messages
    #         # For brevity, we assume the summarizer service will fetch the required segment.
    #     },
    #     queue=IncrementalSummarizerRequest.queue
    # )

    logger.info("Task %s: TR Agent events published successfully.", task_id)


@celery_app.task(name=InitiationEAStreamRequest.name, ignore_result=True)
def handle_initiation_ea_stream_request_event(event_type: str, payload: dict):
    """
    Consumer task for INITIATION_EA_STREAM_REQUEST.

    1. Executes the Explorer Agent (EA) and streams the response text.
    2. Publishes INITIATION_STREAM_COMPLETED event to transfer control to SKE computation.
    """
    task_id = handle_initiation_ea_stream_request_event.request.id

    # Extract necessary fields for EA (Dialogue focused)
    session_id = payload.get('session_id')
    user_id = payload.get('user_id', None)
    user_message = payload.get('user_message')
    agent_role_name = payload.get('ea_agent_role_name')
    current_chat_history = payload.get('current_chat_history', [])

    if not all([session_id, user_message]):
        logger.error("Task %s: Missing critical fields in payload. Aborting.", task_id)
        return

    if agent_role_name is None:
        logger.error("Task %s: Missing Explorer agent role name. Aborting.", task_id)
        return

    if user_id is None:
        logger.error("Task %s: Missing user_id in payload. Aborting.", task_id)
        return

    logger.info("Task %s: Starting EA streaming for session %s.", task_id, session_id)

    persist_chat_entry_payload = {
        "session_id": session_id,
        "role": "user",
        "content": user_message,
        "name": "User",
        "sequence_number": len(current_chat_history) + 1,
    }
    publish_event.delay(
        event_type=PersistChatEntry.name,
        payload=persist_chat_entry_payload,
        queue=PersistChatEntry.queue
    )

    agent, role_config = get_agent_instance(AgentRoleConfig, agent_role_name)
    try:
        response_stream = agent.generate_stream(
            message=Message(role="user", content=user_message, name="User"),
            chat_history=[Message(**msg) for msg in current_chat_history]
        )
        full_response_text = ""
        for chunk in response_stream:
            text_chunk = chunk.content if chunk.content else ""
            full_response_text += text_chunk
            send_ws_notification(
                user_id=user_id,
                event_type="initiation_ea_stream",
                payload={
                    "message": "Initiation EA streaming in progress.",
                    "status": "RUNNING",
                    'full_response_text': full_response_text
                }
            )

        send_ws_notification(
            user_id=user_id,
            event_type="initiation_ea_stream",
            payload={
                "message": "Initiation EA streaming complete.",
                "status": "COMPLETE",
                'full_response_text': full_response_text
            }
        )
        logger.info("Task %s: EA streaming complete.", task_id)
    except Exception as e:
        logger.critical("Task %s: EA streaming failed for session %s: %s", task_id, session_id, str(e))

    persist_chat_entry_payload = {
        "session_id": session_id,
        "role": "system",
        "content": full_response_text,
        "name": agent_role_name,
        "sequence_number": len(current_chat_history) + 2,
    }
    publish_event.delay(
        event_type=PersistChatEntry.name,
        payload=persist_chat_entry_payload,
        queue=PersistChatEntry.queue
    )

    # # Publish Event to Trigger SKE Computation
    # # SKE Task needs the full text and all decision context
    # ske_request_payload = {
    #     "session_id": session_id,
    #     "user_message": user_message,
    #     "full_response_text": full_response_text, # Key input for SKE analysis

    #     # Pass all DA decision context from original payload
    #     "user_id": user_id,
    #     "current_clarity_score": payload.get('current_clarity_score'),
    #     "last_da_execution_time": payload.get('last_da_execution_time'),
    #     "da_activation_threshold": payload.get('da_activation_threshold'),
    # }

    # # Publish event to trigger the SKE Task (handle_ske_extraction_task)
    # publish_event.delay(
    #     event_type=InitiationEAStreamCompleted.name,
    #     payload=ske_request_payload,
    #     queue=InitiationEAStreamCompleted.queue
    # )
    # logger.info("Task %s: Published %s event to trigger SKE extraction.", task_id, InitiationEAStreamCompleted.name)
