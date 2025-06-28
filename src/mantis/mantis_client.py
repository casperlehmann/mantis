from pathlib import Path
from assistant.assistant import Assistant
from mantis.cache import Cache
from mantis.http import Http
from mantis.jira.jira_client import JiraClient
from mantis.openai_client import OpenAIClient
from mantis.options_loader import OptionsLoader


class MantisClient:

    def __init__(self, options: "OptionsLoader", no_read_cache: bool = False):
        self.options = options
        self._no_read_cache = no_read_cache
        self.drafts_dir.mkdir(exist_ok=True)
        self.plugins_dir.mkdir(exist_ok=True)
        self.cache = Cache(self)
        self.jira = JiraClient(self)
        self.http = Http(self, no_read_cache)
        self.assistant = Assistant(self)
        self.open_ai_client = OpenAIClient(self)

    @property
    def drafts_dir(self) -> Path:
        return Path(self.options.drafts_dir)

    @property
    def plugins_dir(self) -> Path:
        return Path(self.options.plugins_dir)
