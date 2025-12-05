import logging

from auraflux_core.core.schemas.messages import Message
from core.celery_app import celery_app
from django.core.cache import cache
from messaging.constants import (InitiationEAStreamRequest, PersistChatEntry,
                                 TopicRefinementAgentRequest,
                                 TopicStabilityUpdated)
from messaging.tasks import publish_event
from realtime.utils import send_ws_notification

from .models import AgentRoleConfig
from .utils import (get_agent_instance, get_agent_response,
                    get_handle_topic_refinement_agent_request_key)

logger = logging.getLogger(__name__)


@celery_app.task(name=TopicRefinementAgentRequest.name, ignore_result=True)
def handle_topic_refinement_agent_request(event_type: str, payload: dict):
    """
    Consumer task for TOPIC_REFINEMENT_AGENT_REQUEST.

    1. Executes the Topic Refinement Agent (TR Agent) to get structured JSON output.
    2. Publishes TOPIC_STABILITY_UPDATED event for persisting structured data (Sidebar update).
    3. Publishes a new event to trigger the Incremental Summarizer Agent.
    """
    session_id = payload.get('session_id', '')
    lock_key = get_handle_topic_refinement_agent_request_key(session_id)
    if cache.get(lock_key):
        return
    else:
        cache.set(lock_key, event_type)

    task_id = handle_topic_refinement_agent_request.request.id
    chat_history = payload.get('recent_turns_of_chat_history')
    conversation_summary_of_old_history = payload.get('conversation_summary_of_old_history')

    # Extract necessary fields for TR Agent (Structured output focused)
    tr_agent_role_name = payload.get('tr_agent_role_name')
    # Context required for TR Agent: full prompt template data, including history, summary, etc.
    tr_agent_input_data = {
        'final_question_draft': payload.get('final_question_draft'),
        'locked_keywords_list': payload.get('locked_keywords_list'),
        'locked_scope_elements_list': payload.get('locked_scope_elements_list'),
        'conversation_summary_of_old_history': conversation_summary_of_old_history,
        'latest_reflection_entry': payload.get('latest_reflection_entry'),
        'recent_turns_of_chat_history': chat_history,
        'latest_user_input': payload.get('latest_user_input')
    }
    user_id = payload.get('user_id') # Required for error notifications if needed

    if chat_history is None:
        logger.error("Task %s: Missing chat history for TR Agent. Aborting.", task_id)
        return

    logger.info("Task %s: Starting TR Agent execution for session %s.", task_id, session_id)

    tr_agent_output_json = get_agent_response(
        AgentRoleConfig,
        tr_agent_role_name,
        rendered_data=tr_agent_input_data,
        output_format='json'
    )

    logger.info("Task %s: Starting SUM Agent execution for session %s.", task_id, session_id)

    sum_agent_role_name = payload.get('sum_agent_role_name')
    rendered_data = {
        "existing_summary": conversation_summary_of_old_history,
        "new_conversation_segment": chat_history,
        "current_structured_state": {
            'final_question_draft': payload.get('final_question_draft'),
            'locked_keywords_list': payload.get('locked_keywords_list'),
            'locked_scope_elements_list': payload.get('locked_scope_elements_list'),
        }
    }
    sum_agent_output_json = get_agent_response(
        AgentRoleConfig,
        sum_agent_role_name,
        rendered_data=rendered_data,
        output_format='json'
    )

    current_research_question = tr_agent_output_json.get('current_research_question')
    topic_stability_updated_payload = {
        "session_id": session_id,
        "new_stability_score": tr_agent_output_json.get('new_stability_score'),
        'is_topic_too_niche': tr_agent_output_json.get('is_topic_too_niche'),
        'current_research_question': '' if current_research_question is None else current_research_question,
        'refined_keywords_to_lock': tr_agent_output_json.get('refined_keywords_to_lock'),
        'refined_scope_to_lock': tr_agent_output_json.get('refined_scope_to_lock'),
        'updated_summary': sum_agent_output_json.get('updated_summary', ''),
        'last_chat_sequence_number': chat_history[-1]['sequence_number']
    }

    # Publish event to update the sidebar/DB (Topic Stability Data)
    publish_event.delay(
        event_type=TopicStabilityUpdated.name,
        payload=topic_stability_updated_payload,
        queue=TopicStabilityUpdated.queue
    )

    cache.delete(lock_key)
    logger.info("Task %s: update topic stability events published successfully.", task_id)

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
    last_analysis_sequence_number = payload.get('last_analysis_sequence_number', 0)

    current_chat_history_length = len(current_chat_history)

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
        "sequence_number": current_chat_history_length + 1,
    }
    current_chat_history.append(persist_chat_entry_payload)
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
        "sequence_number": current_chat_history_length + 2,
    }
    current_chat_history.append(persist_chat_entry_payload)
    publish_event.delay(
        event_type=PersistChatEntry.name,
        payload=persist_chat_entry_payload,
        queue=PersistChatEntry.queue
    )

    if current_chat_history_length - 5 > last_analysis_sequence_number:
        recent_turns_of_chat_history = current_chat_history[last_analysis_sequence_number:]
    else:
        recent_turns_of_chat_history = current_chat_history[-7:]

    tr_agent_request_payload = {
        'session_id': session_id,
        'tr_agent_role_name': 'ResearchTopicRefinementAgent',
        'sum_agent_role_name': 'IncrementalConversationSummarizer',
        'user_id': user_id,
        'final_question_draft': payload.get('final_question_draft'),
        'locked_keywords_list': payload.get('locked_keywords_list'),
        'locked_scope_elements_list': payload.get('locked_scope_elements_list'),
        'conversation_summary_of_old_history': payload.get('conversation_summary_of_old_history'),
        'latest_reflection_entry': payload.get('latest_reflection_entry'),
        'recent_turns_of_chat_history': recent_turns_of_chat_history,
        'latest_user_input': user_message
    }

    # Publish event to trigger the Topic Refinement Agent
    publish_event.delay(
        event_type=TopicRefinementAgentRequest.name,
        payload=tr_agent_request_payload,
        queue=TopicRefinementAgentRequest.queue
    )
    logger.info("Task %s: Published %s event to trigger TR Agent.", task_id, TopicRefinementAgentRequest.name)
