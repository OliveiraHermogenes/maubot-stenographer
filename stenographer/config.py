from typing import Callable

from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper


class Config(BaseProxyConfig):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize on_update
        self.on_update = None

    def do_update(self, helper: ConfigUpdateHelper) -> None:
        helper.copy("base_url")
        helper.copy("model_name")
        helper.copy("api_key")
        helper.copy("language")
        helper.copy("translate")

        # If on_update is set, call it
        if self.on_update is not None:
            self.on_update()

    def set_on_update(self, on_update: Callable[[], None]) -> None:
        """
        Set a callable that will be called whenever the config is updated (including for the first time).
        Should be called before `load_and_update()`
        """
        self.on_update = on_update
