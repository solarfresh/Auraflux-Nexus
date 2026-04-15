class Queue:
    DEFAULT = 'default'
    STREAM = 'stream'


class AgentRequest:
    name = "handle_agent_request"
    queue = Queue.DEFAULT


class CreateNewCanvas:
    name = 'create_new_canvas'
    queue = Queue.DEFAULT


class GetRecommendedConceptualNodes:
    name = "get_recommended_conceptual_nodes"
    queue = Queue.DEFAULT


class InitiationEAStreamRequest:
    name = "handle_initiation_ea_stream_request_event"
    queue = Queue.STREAM


class PersistChatEntry:
    name = "persist_chat_entry"
    queue = Queue.DEFAULT


class RecommendConceptualNodes:
    name = "handle_recommend_conceptual_nodes_request"
    queue = Queue.DEFAULT


class TopicRefinementAgentRequest:
    name = "handle_topic_refinement_agent_request"
    queue = Queue.DEFAULT


class TopicStabilityUpdated:
    name = 'update_topic_stability_data'
    queue = Queue.DEFAULT


class UpdateModelFamilies:
    name = "update_model_families"
    queue = Queue.DEFAULT
