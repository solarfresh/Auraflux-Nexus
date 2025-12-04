import logging
from datetime import datetime

from asgiref.sync import async_to_sync
from auraflux_core.core.schemas.messages import Message
from core.celery_app import celery_app
from django.utils import timezone
from messaging.constants import (InitiationEAStreamCompleted,
                                 InitiationEAStreamRequest,
                                 InitiationSKEResponseComputed,
                                 PersistChatEntry)
from messaging.tasks import publish_event
from realtime.utils import send_ws_notification

from .utils import get_agent_instance

logger = logging.getLogger(__name__)


@celery_app.task(name=InitiationEAStreamCompleted.name, ignore_result=True)
def handle_initiation_ea_stream_complete_event(event_type: str, payload: dict):
    """
    Consumer task for INITIATION_EA_STREAM_COMPLETED.

    1. Executes SKE Agent to calculate s_new and k_pre.
    2. Performs the DA activation check.
    3. Publishes INITIATION_SKE_RESPONSE_COMPUTED for DB update.
    4. Publishes INITIATION_DA_VALIDATION_REQUESTED if needed.
    """
    task_id = handle_initiation_ea_stream_complete_event.request.id

    # Extract Context Data
    session_id = payload.get('session_id')
    user_id = payload.get('user_id')
    agent_role_name = payload.get('ske_agent_role_name')
    current_chat_history = payload.get('current_chat_history', [])
    full_response_text = payload.get('full_response_text', '') # Key data from streaming task

    # Extract DA Decision Context
    clarity_score_old = payload.get('current_clarity_score', 0.0)
    da_threshold = payload.get('da_activation_threshold', 0.35)
    last_da_execution_time_str = payload.get('last_da_execution_time')

    if agent_role_name is None:
        logger.error("Task %s: Missing SKE agent role name. Aborting.", task_id)
        return

    if not full_response_text:
        logger.error("Task %s: Missing full_response_text. Cannot perform SKE analysis.", task_id)
        return

    # --- Execute SKE Computation ---
    s_new = clarity_score_old
    k_pre = []

    agent = get_agent_instance(agent_role_name)

    try:
        current_chat_history.append(full_response_text)
        messages = [Message(**msg) for msg in current_chat_history]

        ske_output = async_to_sync(agent.generate)(messages=messages)
        s_new = ske_output.get('clarity_score', clarity_score_old)
        k_pre = ske_output.get('extracted_keywords', [])
        logger.info("Task %s: SKE computation complete. S_new: %.2f", task_id, s_new)

    except Exception as e:
        logger.critical("Task %s: SKE execution failed: %s", task_id, str(e))
        # Fallback to old values

    # --- Determine DA Activation ---
    should_trigger_da = False
    # Clarity Score Threshold
    if s_new > da_threshold:
        # Time elapsed threshold (M seconds) - Logic simplified here
        time_elapsed_ok = True
        if last_da_execution_time_str:
            last_da_execution_time = datetime.fromisoformat(last_da_execution_time_str)
            time_since_last_run = (timezone.now() - last_da_execution_time).total_seconds()

            # Assuming M=60 seconds as the interval
            if time_since_last_run < 60:
                time_elapsed_ok = False

        # Keyword Stability Count (N turns) - Requires DB lock, deferred
        # We rely on the DB write task to perform the final check under lock.
        if time_elapsed_ok:
            # We preliminarily set the flag. The DB write task will finalize the decision.
            should_trigger_da = True

    # --- Publish SKE Response Computed ---
    ske_response_payload = {
        "session_id": session_id,
        "user_id": user_id,
        "ai_response_text": full_response_text, # R (for DB history logging)
        "new_clarity_score": s_new,
        "new_unverified_keywords": k_pre,

        # Pass the preliminary DA trigger flag to the DB write task
        "preliminary_da_trigger": should_trigger_da,
        "last_da_execution_time": last_da_execution_time_str, # Pass context for final lock check
        # ... (Pass any other necessary DA context)
    }

    # This triggers the high-priority DB write task
    publish_event.delay(
        event_type=InitiationSKEResponseComputed.name,
        payload=ske_response_payload,
        queue=InitiationSKEResponseComputed.queue
    )
    logger.info("Task %s: Published %s event for DB update.", task_id, InitiationSKEResponseComputed.name)

    # --- Publish DA Validation Request ---
    # To maintain consistency, the final decision and submission of DA is best done
    # within the DB write task (INITIATION_SKE_RESPONSE_COMPUTED consumer)
    # after the atomic update. We omit the direct submission here and let the
    # DB task handle the final trigger.

    # If the DB task confirms the DA trigger, it will publish INITIATION_DA_VALIDATION_REQUESTED.
    if should_trigger_da:
        logger.warning("Task %s: Preliminary DA trigger flag set. Awaiting DB confirmation.", task_id)

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

    agent = get_agent_instance(agent_role_name)
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
