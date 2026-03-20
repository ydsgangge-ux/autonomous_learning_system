from llm.client import llm_client
from typing import List, Dict

async def mindmap_to_text(mindmap: Dict) -> str:
    """Convert mindmap structure to readable text."""
    lines = [f"# {mindmap.get('central', 'Mindmap')}"]
    branches = mindmap.get('branches', [])

    def format_branch(branch, prefix="", is_last=True):
        result = []
        name = branch.get('name', '')
        children = branch.get('children', [])

        connector = "└── " if is_last else "├── "
        result.append(f"{prefix}{connector}{name}")

        child_prefix = prefix + ("    " if is_last else "│   ")
        for i, child in enumerate(children):
            result.extend(format_branch(child, child_prefix, i == len(children) - 1))

        return result

    for i, branch in enumerate(branches):
        lines.extend(format_branch(branch, "", i == len(branches) - 1))

    return "\n".join(lines)


async def generate_mindmap(topic: str) -> Dict:
    """Generate a mindmap structure for a given topic using LLM."""
    prompt = f"""Create a mindmap for the topic "{topic}". 
Return a JSON object with a central node and branches.
Example:
{{
  "central": "{topic}",
  "branches": [
    {{"name": "subtopic1", "children": [{{"name": "detail1"}}]}},
    {{"name": "subtopic2"}}
  ]
}}
"""
    messages = [{"role": "user", "content": prompt}]
    schema = {"type": "object", "properties": {"central": {"type": "string"}, "branches": {"type": "array"}}}
    result = await llm_client.structured_output(messages, schema)
    return result
