# agent/services/title_generator.py

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from app.agent.llm.gateway import LLMGateway


class TitleOutput(BaseModel):
    title: str = Field(min_length=3, max_length=80)
    description: str = Field(min_length=8, max_length=220)


async def generate_conversation_title(
    llm: LLMGateway, workflow, params: dict
) -> tuple[str, str]:
    name = getattr(workflow, "name", "workflow")
    fallback_title = name.replace("_", " ").strip().title() + " Run"
    fallback_desc = f"Run `{name}` with the provided parameters."

    try:
        mini = llm.create_mini()
        base = getattr(mini, "_llm", None)
        if base is None:
            return fallback_title, fallback_desc

        preview = ", ".join(
            f"{k}={repr(v)[:77]}" for k, v in list(params.items())[:8]
        ) or "None"

        result = await base.with_structured_output(TitleOutput).ainvoke([
            SystemMessage(content=(
                "Generate concise conversation metadata for a "
                "backend workflow run. No markdown or quotes."
            )),
            HumanMessage(content=(
                f"Workflow: {name}\n"
                f"Description: {getattr(workflow, 'description', '')}\n"
                f"Params: {preview}\n\n"
                "Return title (3-8 words) and description (one sentence)."
            )),
        ])
        return (
            result.title.strip().strip("\"'") or fallback_title,
            result.description.strip().strip("\"'") or fallback_desc,
        )
    except Exception:
        return fallback_title, fallback_desc
