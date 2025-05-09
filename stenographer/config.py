from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper

class Config(BaseProxyConfig):
    def do_update(self, helper: ConfigUpdateHelper) -> None:
        helper.copy("base_url")
        helper.copy("model_name")
        helper.copy("api_key")
        helper.copy("language")
        helper.copy("reaction")
        helper.copy("auto")
