"""
Magik Text Save - standalone ComfyUI custom node package.

Drop this folder into ComfyUI/custom_nodes/ as-is; it has no dependency on
any other Magik package.
"""

from typing_extensions import override
from comfy_api.latest import ComfyExtension, io

from .magik_text_save import Magik_Text_Save


class MagikTextSaveExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [Magik_Text_Save]


async def comfy_entrypoint() -> MagikTextSaveExtension:
    return MagikTextSaveExtension()
