class Queue:
    DEFAULT = 'default'
    STREAM = 'stream'


class InitiationEAStreamRequest:
    name = "handle_initiation_ea_stream_request_event"
    queue = Queue.STREAM


class InitiationEAStreamCompleted:
    name = "handle_initiation_ea_stream_complete_event"
    queue = Queue.DEFAULT


class InitiationSKEResponseComputed:
    name = ""
    queue = Queue.DEFAULT

# INITIATION_CHAT_INPUT_REQUESTED = "handle_initiation_chat_input_request_event"
# INITIATION_DA_VALIDATION_REQUESTED = ""
# INITIATION_EA_STREAM_REQUEST = "handle_initiation_ea_stream_request_event"
# INITIATION_EA_STREAM_COMPLETED = "handle_initiation_ea_stream_complete_event"
# INITIATION_EA_RESPONSE_COMPUTED = ""
# INITIATION_SKE_RESPONSE_COMPUTED = ""