from urlextract import URLExtract


class MessageBuilder:
    def __init__(self, message: str) -> None:
        self._message = message

    def build(self):
        extractor = URLExtract()
        urls = extractor.find_urls(self._message, only_unique=True)

        for url in urls:
            self._message = self._message.replace(
                url, f'<a href="{url}">{url}</a>'  # type: ignore
            )

        return self._message
