from django.db import models


class SearchResult(models.Model):
    """
    Represents a single search result item.
    """
    query = models.CharField(max_length=255, db_index=True, help_text="The search query that this result is associated with.")
    title = models.CharField(max_length=255, help_text="The title of the search result.")
    description = models.TextField(help_text="A brief description or summary of the content.")
    link = models.URLField(max_length=500, help_text="The URL to the original source.")
    source = models.CharField(max_length=100, help_text="The source of the result (e.g., '創業小聚').")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "Search Results"
