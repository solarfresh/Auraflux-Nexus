import pytest
from uuid import uuid4

from canvases.tasks import handle_recommend_conceptual_edges_request
from messaging.constants import AgentRequest, GetRecommendedConceptualNodes, RecommendConceptualEdges


@pytest.mark.django_db
class TestHandleRecommendConceptualEdgesRequest:
    """
    Refactored test suite utilizing centralized conftest fixtures
    to verify edge recommendation orchestration logic.
    """

    @pytest.fixture
    def base_payload(self):
        """Provides a standard baseline setup for the pipeline event payload."""
        return {
            "user_id": uuid4(),
            "canvas_id": uuid4(),
            "on_canvas_str": "- [EVENT] Old Action (id: node-1)",
            "on_canvas_ids": ["node-1"],
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

    def test_routes_to_autonomous_weaver_agent_on_other_modes(self, mock_external_infrastructure, base_payload):
        """
        Verify that non-directed recommendation modes (e.g., 'autonomous')
        fallback securely to routing via the 'AutonomousWeaverAgent'.
        """
        base_payload["recommendation_mode"] = "autonomous"
        mock_publish = mock_external_infrastructure["canvas_publish"]

        handle_recommend_conceptual_edges_request("test_event", base_payload)

        mock_publish.assert_called_once()
        emitted_payload = mock_publish.call_args[1]["payload"]
        assert emitted_payload["agent_role_name"] == "AutonomousWeaverAgent"

    def test_filters_outlyer_floating_nodes_correctly(self, mock_external_infrastructure, base_payload):
        """
        Ensure nodes matching existing on-canvas IDs are filtered out,
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

        # Validate structural markdown formatting
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