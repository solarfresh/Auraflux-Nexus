from django.db import models


class AgentRoleConfig(models.Model):
    """
    Defines the specific role, behavior, and LLM parameters for an agent type
    (e.g., 'Dichotomy Suggester', 'Scope Summarizer').
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="The unique name used to identify this agent role (e.g., 'Dichotomy Suggester')."
    )

    # Core behavior settings
    system_prompt = models.TextField(
        help_text="The instruction set given to the LLM to define its persona and task."
    )
    output_schema = models.JSONField(
        help_text="The JSON schema defining the required output structure for the LLM response."
    )

    # Runtime generation parameters (overrides/additions to ModelConfig)
    llm_parameters = models.JSONField(
        default=dict,
        blank=True,
        help_text="Specific runtime parameters for the LLM call (e.g., temperature, top_p, max_tokens)."
    )

    class Meta:
        verbose_name = "Agent Role Configuration"
        verbose_name_plural = "Agent Role Configurations"

    def __str__(self):
        return self.name
