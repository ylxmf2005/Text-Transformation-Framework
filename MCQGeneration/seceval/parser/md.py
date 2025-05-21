from seceval.entity import PageItem, TextArtifact, gen_uuid
from typing import Any, List, Dict


class MdParser:
    def __init__(self, profile: Dict[str, Any] = {}):
        self.max_level = profile.get("max_level", 3)

    def parse(self, item: PageItem):
        assert item.content is not None
        md = item.content.content.decode("utf-8")
        header_stack: List[TextArtifact] = []
        artifacts: List[TextArtifact] = []
        current_text = ""
        minumum_level = 100
        for line in md.split("\n"):
            if line.startswith("#"):
                minumum_level = min(len(line) - len(line.lstrip("#")), minumum_level)

        for line in md.split("\n"):
            level = len(line) - len(line.lstrip("#"))
            level = level - minumum_level + 1

            if line.startswith("#") and level <= self.max_level:  # header line
                if current_text.strip():  # if there is text for the current artifact
                    artifact = TextArtifact(
                        page_id=item.id,
                        page_uri=item.uri or item.file_path,
                        page_depth=item.depth,
                        page_type=item.type,
                        id=header_stack[-1].id if header_stack else gen_uuid(),
                        index=len(artifacts),
                        level=header_stack[-1].level if header_stack else 1,
                        title=header_stack[-1].title if header_stack else "",
                        parent_id=header_stack[-1].parent_id if header_stack else None,
                        html="",
                        text=current_text.strip(),
                    )
                    artifacts.append(artifact)
                    current_text = ""

                # update the stack of headers
                while header_stack and (header_stack[-1].level) >= level:
                    header_stack.pop()
                header_stack.append(
                    TextArtifact(
                        page_id=item.id,
                        page_uri=item.uri or item.file_path,
                        page_depth=item.depth,
                        page_type=item.type,
                        id=gen_uuid(),
                        title=line.lstrip("# ").strip(),
                        level=header_stack[-1].level + 1 if header_stack else 1,
                        parent_id=header_stack[-1].id if header_stack else None,
                        html="",
                        text="",
                    )
                )
                current_text += line + "\n"
            else:  # non-header line
                current_text += line + "\n"

        # Add the last artifact
        if current_text.strip():
            artifact = TextArtifact(
                page_id=item.id,
                page_uri=item.uri or item.file_path,
                page_depth=item.depth,
                page_type=item.type,
                id=item.id if len(artifacts) == 0 else gen_uuid(),
                level=header_stack[-1].level + 1 if header_stack else 1,
                index=len(artifacts),
                title=header_stack[-1].title if header_stack else "",
                parent_id=header_stack[-1].parent_id if header_stack else None,
                html="",
                text=current_text.strip(),
            )
            artifacts.append(artifact)

        return artifacts
