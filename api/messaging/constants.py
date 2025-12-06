class Queue:
    DEFAULT = 'default'
    STREAM = 'stream'

class InitiationEAStreamRequest:
    name = "handle_initiation_ea_stream_request_event"
    queue = Queue.STREAM


class TopicRefinementAgentRequest:
    name = "handle_topic_refinement_agent_request"
    queue = Queue.DEFAULT


class TopicStabilityUpdated:
    name = 'update_topic_stability_data'
    queue = Queue.DEFAULT


class PersistChatEntry:
    name = "persist_chat_entry"
    queue = Queue.DEFAULT
