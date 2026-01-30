class WebParser:
    """Parse raw HTML into structured content."""

    async def run(self, content: str) -> dict:
        return {"text": content}
