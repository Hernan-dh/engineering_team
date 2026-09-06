"""Optional web search for architecture and dependency research."""

from __future__ import annotations

import os

import requests
from crewai.tools import BaseTool
from ddgs import DDGS
from pydantic import BaseModel, Field


class WebSearchInput(BaseModel):
    query: str = Field(..., description="A focused architecture, framework, or dependency query.")


class WebSearchTool(BaseTool):
    name: str = "web_search"
    description: str = (
        "Search current technical documentation and compatibility information. "
        "Use it for architecture decisions or dependency questions not settled by local files."
    )
    args_schema: type[BaseModel] = WebSearchInput

    def _run(self, query: str) -> str:
        api_key = os.getenv("SERPER_API_KEY")
        if api_key:
            response = requests.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
                json={"q": query, "num": 4}, timeout=10,
            )
            response.raise_for_status()
            normalized = [(i.get("title", ""), i.get("link", ""), i.get("snippet", ""))
                          for i in response.json().get("organic", [])]
            provider = "Serper"
        else:
            normalized = [(i.get("title", ""), i.get("href", ""), i.get("body", ""))
                          for i in DDGS(timeout=10).text(query, max_results=4)]
            provider = "DDGS"
        usable = [(title, url, snippet) for title, url, snippet in normalized if url]
        if not usable:
            return "No usable search results found."
        return "\n\n".join(f"[{provider}] {title}\n{snippet}\nURL: {url}" for title, url, snippet in usable)
