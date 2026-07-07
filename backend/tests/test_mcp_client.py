from app.services.mcp.client import MicrosoftLearnMCPClient


def test_extract_text_items_from_tool_content() -> None:
    raw = {
        "content": [
            {"type": "text", "text": '{"title":"Azure Functions","url":"https://learn.microsoft.com/azure/azure-functions/"}'},
            {"type": "text", "text": "plain reference"},
        ]
    }

    items = MicrosoftLearnMCPClient._extract_text_items(raw)

    assert items == [
        '{"title":"Azure Functions","url":"https://learn.microsoft.com/azure/azure-functions/"}',
        "plain reference",
    ]


def test_coerce_reference_normalizes_known_mcp_shapes() -> None:
    reference = MicrosoftLearnMCPClient._coerce_reference(
        {
            "name": "Azure Functions docs",
            "contentUrl": "https://learn.microsoft.com/azure/azure-functions/",
            "snippet": "Serverless compute documentation.",
            "id": "azure-functions",
        },
        "Azure Functions",
    )

    assert reference == {
        "title": "Azure Functions docs",
        "url": "https://learn.microsoft.com/azure/azure-functions/",
        "content": "Serverless compute documentation.",
        "source": "learn.microsoft.com",
        "document_id": "azure-functions",
    }


async def test_resolve_search_tool_prefers_docs_search_tool() -> None:
    client = MicrosoftLearnMCPClient(server_url="https://example.test/mcp")

    async def fake_list_tools() -> list[dict[str, str]]:
        return [
            {"name": "other_search"},
            {"name": "microsoft_docs_search"},
        ]

    client.list_tools = fake_list_tools  # type: ignore[method-assign]

    assert await client._resolve_search_tool() == "microsoft_docs_search"
