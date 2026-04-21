import uuid
import os

from django.db import models
from core.models import BaseModel
from django.contrib.auth import get_user_model
from core.constants import ConnectStatus
from agents.constants import ProviderType
from cryptography.fernet import Fernet
from django.conf import settings

User = get_user_model()


class AgentRoleConfig(BaseModel):
    """
    Defines the specific role, behavior, and LLM parameters for an agent type
    (e.g., 'Dichotomy Suggester', 'Scope Summarizer').
    """
    name = models.CharField(
        max_length=100,
    )

    role = models.CharField(
        max_length=100,
        unique=True,
        help_text="The unique name used to identify this agent role (e.g., 'Dichotomy Suggester')."
    )

    # Core behavior settings
    system_prompt = models.TextField(
        help_text="The instruction set given to the LLM to define its persona and task."
    )

    # Stores the full prompt text with placeholders (e.g., {{final_question_draft}})
    prompt_template = models.TextField(
        null=True,
        blank=True,
        help_text="The full template text used to render the final prompt, containing all static text and {{variable}} placeholders."
    )

    # Defines what data needs to be fetched for the template placeholders.
    template_variables = models.JSONField(
        default=dict,
        blank=True,
        help_text="A dictionary defining the dynamic variables required by the prompt_template and their data source/type (e.g., {'final_question_draft': 'DB_FACTS', 'latest_user_input': 'CURRENT_TURN'})."
    )

    output_schema = models.JSONField(
        help_text="The JSON schema defining the required output structure for the LLM response."
    )

    llm_parameters = models.JSONField(
        default=dict,
        blank=True,
        help_text="Specific runtime parameters for the LLM call (e.g., temperature, top_p, max_tokens)."
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        help_text="The ID of the user owning this project."
    )

    projects = models.ManyToManyField(
        'projects.ResearchProject',
        related_name='agent',
        through='AgentProjectRelation',
    )

    class Meta:
        verbose_name = "Agent Role Configuration"
        verbose_name_plural = "Agent Role Configurations"

    def __str__(self):
        return self.name


class AgentProjectRelation(BaseModel):

    agent = models.ForeignKey(
        'AgentRoleConfig',
        on_delete=models.CASCADE
    )
    project = models.ForeignKey(
        'projects.ResearchProject',
        on_delete=models.CASCADE
    )


class ModelFamilies(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    input_token_limit = models.PositiveIntegerField()
    output_token_limit = models.PositiveIntegerField()


class ModelProvider(BaseModel):
    # --- Engine Identity ---
    name = models.CharField(max_length=100)
    provider_type = models.CharField(
        max_length=20,
        choices=ProviderType.choices,
        default=ProviderType.GOOGLE
    )

    # --- Infrastructure & Security ---
    _encrypted_api_key = models.TextField(db_column='api_key', blank=True, null=True)
    base_url = models.URLField(blank=True, null=True)

    # --- Diagnostics (Rule 14: Pulse) ---
    status = models.CharField(
        max_length=20,
        choices=ConnectStatus.choices,
        default=ConnectStatus.UNVERIFIED
    )
    latency_ms = models.PositiveIntegerField(blank=True, null=True)
    last_verified_at = models.DateTimeField(blank=True, null=True)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        help_text="The ID of the user owning this provider."
    )
    supported_families = models.ManyToManyField(
        ModelFamilies,
        blank=True
    )
    active_agent = models.ManyToManyField(
        AgentRoleConfig,
        blank=True
    )

    # --- Audit ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.provider_type})"

    # --- Security Logic (Cognitive Sovereignty) ---

    def _get_fernet(self):
        key = os.getenv('ENCRYPTION_KEY_64', settings.SECRET_KEY[:32].encode('utf-8').ljust(32, b'='))
        import base64
        if isinstance(key, str):
            key = key.encode()
        return Fernet(base64.urlsafe_b64encode(key[:32]))

    def set_api_key(self, raw_key: str):
        if not raw_key:
            self._encrypted_api_key = None
        else:
            fernet = self._get_fernet()
            self._encrypted_api_key = fernet.encrypt(raw_key.encode()).decode()

    def get_api_key(self) -> str:
        if not self._encrypted_api_key:
            return ""
        try:
            fernet = self._get_fernet()
            return fernet.decrypt(self._encrypted_api_key.encode()).decode()
        except Exception:
            return "DECRYPTION_ERROR"

    @property
    def api_key_fingerprint(self):
        raw = self.get_api_key()
        if raw and raw != "DECRYPTION_ERROR":
            return f"••••{raw[-4:]}"
        return None

    @property
    def active_agent_count(self):
        return self.active_agent.count()
