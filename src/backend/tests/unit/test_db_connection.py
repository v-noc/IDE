import respx
import httpx
import pytest


@pytest.mark.asyncio
async def test_info(client):

    result = await client.info()
    assert result["api:status"] == "api:success"


@pytest.mark.asyncio
async def test_streaming_query(client):
    some_woql = {
        "@type": "Equals",
        "left": {
            "@type": "DataValue",
            "variable": "Message"
        },
        "right": {
            "@type": "DataValue",
            "data": {
                "@type": "xsd:string",
                "@value": "Hello from an empty database!"
            }
        }
    }
    result = await client.query(some_woql, streaming=True)
    async for binding in result:
        print(f"binding-: {binding}")
        assert binding["@type"] == "Binding"
