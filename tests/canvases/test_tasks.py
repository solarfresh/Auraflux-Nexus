from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from canvases.models import CanvasNodeRelation, ConceptualNode
from canvases.tasks import handle_recommend_conceptual_edges_request
from messaging.constants import AgentRequest


@pytest.mark.django_db
class TestHandleRecommendConceptualEdgesRequest:
    """
    Refactored test suite utilizing centralized conftest fixtures
    to verify edge recommendation orchestration logic across directed
    and autonomous recommendation modes.
    """

    @pytest.fixture
    def base_payload(self):
        """Provides a standard baseline setup for the pipeline event payload."""
        return {
            "user_id": str(uuid4()),
            "canvas_id": str(uuid4()),
            "on_canvas_str": "- [EVENT] Old Action (id: node-1)",
            "on_canvas_ids": ["node-1"],
            "newly_onboarded_nodes": [
                {"id": "node-2", "type": "INSIGHT", "label": "New Finding"},
                {"id": "node-3", "type": "OUTCOME", "label": "Goal Result"}
            ],
            "agent_output": {
                "nodes": {
                    "node-1": {"id": "node-1", "type": "EVENT", "label": "Old Action", "anchor_id": "a-1"},
                    "node-2": {"id": "node-2", "type": "INSIGHT", "label": "New Finding", "anchor_id": "a-2"},
                    "node-3": {"id": "node-3", "type": "OUTCOME", "label": "Goal Result", "anchor_id": "a-3"}
                },
                "edges": []
            }
        }

    def test_routes_to_directed_weaver_agent(self, mock_external_infrastructure, base_payload):
        """
        Verify that setting recommendation_mode to 'directed' resolves
        the target agent to 'DirectedWeaverAgent' and passes down metadata.
        """
        base_payload["recommendation_mode"] = "directed"
        mock_publish = mock_external_infrastructure["canvas_publish"]

        # Trigger the celery task explicitly
        handle_recommend_conceptual_edges_request("test_event", base_payload)

        mock_publish.assert_called_once()
        kwargs = mock_publish.call_args[1]

        assert kwargs["event_type"] == AgentRequest.name
        assert kwargs["queue"] == AgentRequest.queue

        emitted_payload = kwargs["payload"]
        assert emitted_payload["agent_role_name"] == "DirectedWeaverAgent"

    def test_routes_to_autonomous_weaver_agent(self, mock_external_infrastructure, base_payload):
        """
        Verify that setting recommendation_mode to 'autonomous' resolves
        the target agent to 'AutonomousWeaverAgent' and dynamically queries
        the DB for on-canvas nodes.
        """
        base_payload["recommendation_mode"] = "autonomous"
        mock_publish = mock_external_infrastructure["canvas_publish"]

        mock_node = MagicMock(spec=ConceptualNode)
        mock_node.id = "node-existing"
        mock_node.node_type = "CONCEPT"
        mock_node.label = "Existing Component"

        mock_relation = MagicMock(spec=CanvasNodeRelation)
        mock_relation.node = mock_node

        mock_filter = MagicMock()
        mock_filter.all.return_value = [mock_relation]
        CanvasNodeRelation.objects.filter = MagicMock(return_value=mock_filter)

        handle_recommend_conceptual_edges_request("test_event", base_payload)

        mock_publish.assert_called_once()
        emitted_payload = mock_publish.call_args[1]["payload"]

        assert emitted_payload["agent_role_name"] == "AutonomousWeaverAgent"
        assert "- [CONCEPT] Existing Component (ID: node-existing)" in emitted_payload["agent_input_data"]["on_canvas_str"]

        serialized_new_str = emitted_payload["agent_input_data"]["newly_onboarded_nodes_str"]
        assert "- [INSIGHT] New Finding (id: node-2)" in serialized_new_str
        assert "- [OUTCOME] Goal Result (id: node-3)" in serialized_new_str

    def test_filters_outlyer_floating_nodes_correctly_in_directed_mode(self, mock_external_infrastructure, base_payload):
        """
        Ensure nodes matching existing on-canvas IDs are filtered out under directed mode,
        and only isolated candidates are formatted into the markdown text template.
        """
        base_payload["recommendation_mode"] = "directed"
        base_payload["on_canvas_ids"] = ["node-1"]  # node-1 is already on canvas
        mock_publish = mock_external_infrastructure["canvas_publish"]

        handle_recommend_conceptual_edges_request("test_event", base_payload)

        emitted_payload = mock_publish.call_args[1]["payload"]
        next_payload = emitted_payload["next_event_payload"]

        # Validate node separation in downstream tracking array
        newly_onboarded = next_payload["newly_onboarded_nodes"]
        assert len(newly_onboarded) == 2
        assert any(n["id"] == "node-2" for n in newly_onboarded)
        assert any(n["id"] == "node-3" for n in newly_onboarded)
        assert not any(n["id"] == "node-1" for n in newly_onboarded)

        # Validate structural markdown formatting for directed mode (must include anchor_id)
        serialized_str = emitted_payload["agent_input_data"]["newly_onboarded_nodes_str"]
        expected_line_1 = "- [INSIGHT] New Finding (id: node-2, anchor_id: a-2)"
        expected_line_2 = "- [OUTCOME] Goal Result (id: node-3, anchor_id: a-3)"
        assert expected_line_1 in serialized_str
        assert expected_line_2 in serialized_str

    def test_handles_empty_newly_onboarded_nodes_gracefully(self, mock_external_infrastructure, base_payload):
        """
        Verify operational stability when all oncoming nodes are already tracked on canvas,
        yielding safe empty fallbacks without index errors.
        """
        base_payload["recommendation_mode"] = "directed"
        # Simulate edge case where everything matches the existing architecture
        base_payload["on_canvas_ids"] = ["node-1", "node-2", "node-3"]
        mock_publish = mock_external_infrastructure["canvas_publish"]

        handle_recommend_conceptual_edges_request("test_event", base_payload)

        emitted_payload = mock_publish.call_args[1]["payload"]
        assert emitted_payload["agent_input_data"]["newly_onboarded_nodes_str"] == ""
        assert emitted_payload["next_event_payload"]["newly_onboarded_nodes"] == []

    def test_raises_value_error_on_invalid_mode(self, mock_external_infrastructure, base_payload):
        """
        Ensure the task raises a ValueError immediately if an unsupported
        recommendation mode is supplied.
        """
        base_payload["recommendation_mode"] = "invalid_mode"
        mock_publish = mock_external_infrastructure["canvas_publish"]

        with pytest.raises(ValueError, match="Invalid recommendation_mode: invalid_mode"):
            handle_recommend_conceptual_edges_request("test_event", base_payload)

        # Ensure pipeline execution aborted before publishing any agent events
        mock_publish.assert_not_called()