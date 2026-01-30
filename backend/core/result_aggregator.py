from __future__ import annotations

from typing import Any, Dict, List


class ResultAggregator:
    """Aggregate results from tools or agents."""

    def aggregate(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        combined: Dict[str, Any] = {"items": []}
        for item in results:
            combined["items"].append(item)
        return combined
