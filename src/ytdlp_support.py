"""Small yt-dlp integration helpers shared by search and resolution."""


class SilentYTDLPLogger:
    """Keep expected extractor misses out of the user-facing terminal."""

    def debug(self, _message: str) -> None:
        pass

    def info(self, _message: str) -> None:
        pass

    def warning(self, _message: str) -> None:
        pass

    def error(self, _message: str) -> None:
        pass
