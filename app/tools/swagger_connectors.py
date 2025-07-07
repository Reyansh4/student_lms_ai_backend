import httpx
from langgraph.graph import StateGraph

BASE_URL = "http://localhost:8000"

def register_swagger_tools(workflow: StateGraph, spec: dict):
    """
    Dynamically register each /api/v1/agent operation as a LangGraph tool.
    The agent should supply `details.path_params`, `details.query_params`, and `details.body`.
    """
    paths = spec.get("paths", {})
    agent_paths = {p: m for p, m in paths.items() if p.startswith("/api/v1/agent")}

    def make_tool(path: str, method: str, info: dict):
        name = (info.get("operationId") or
                f"{method}_{path.strip('/').replace('/', '_')}").lower()

        async def _call(state: dict, config: dict):
            details = state.get("details", {}) or {}
            path_params = details.get("path_params", {})
            query_params = details.get("query_params", {})
            body = details.get("body", None)

            try:
                url_path = path.format(**path_params)
            except KeyError as e:
                return {"error": f"Missing path parameter: {e.args[0]}"}

            url = f"{BASE_URL}{url_path}"
            async with httpx.AsyncClient() as client:
                resp = await client.request(
                    method,
                    url,
                    params=query_params or None,
                    json=body if body is not None else None,
                    timeout=10
                )
                resp.raise_for_status()
                try:
                    data = resp.json()
                except ValueError:
                    data = {"text": resp.text}
            return {"data": data}

        workflow.add_node(name, _call)
        workflow.set_finish_point(name)

    for raw_path, methods in agent_paths.items():
        for http_method, info in methods.items():
            make_tool(raw_path, http_method.upper(), info)