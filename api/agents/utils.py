from typing import Any, Optional

# Placeholder for the initialized ClientManager instance
_GLOBAL_CLIENT_MANAGER: Optional[Any] = None

def set_global_client_manager(client_manager: Any):
    """Sets the initialized ClientManager instance."""
    global _GLOBAL_CLIENT_MANAGER
    _GLOBAL_CLIENT_MANAGER = client_manager

def get_global_client_manager() -> Any:
    """Retrieves the initialized ClientManager instance."""
    if _GLOBAL_CLIENT_MANAGER is None:
        raise RuntimeError("ClientManager has not been initialized. Check agents/apps.py ready() method.")
    return _GLOBAL_CLIENT_MANAGER