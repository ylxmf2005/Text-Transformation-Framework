from seceval.entity import PageItem, TextArtifact, gen_uuid


class TextParser:
    def __init__(self, profile: dict = {}):
        pass

    def parse(self, item: PageItem):
        assert item.content is not None
        return [
            TextArtifact(
                page_id=item.id,
                page_uri=item.uri or item.file_path,
                page_depth=item.depth,
                page_type=item.type,
                id=gen_uuid(),
                index=0,
                level=0,
                title="",
                parent_id=None,
                html="",
                text=item.content.content.decode("utf-8"),
            )
        ]
