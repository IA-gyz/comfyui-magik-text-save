"""
Magik Text Save - standalone text saving node for ComfyUI
Built on the same design as Magik Image Save, adapted for saving a single
text string (no batch processing).
"""

import os
import re
import time
from typing import Optional

from comfy_api.latest import io, ui


# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

ALLOWED_EXT = ('.txt', '.json')
DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "output")
DEFAULT_OUTPUT_DIR = os.path.normpath(DEFAULT_OUTPUT_DIR)


# ============================================================================
# LIGHTWEIGHT LOGGING
# ============================================================================

class _Colors:
    END = '\33[0m'
    BLUE = '\33[34m'
    RED = '\33[31m'
    YELLOW = '\33[33m'

def log_msg(msg: str):
    print(f"{_Colors.BLUE}Magik Text Save:{_Colors.END} {msg}")

def log_err(msg: str):
    print(f"{_Colors.RED}Magik Text Save Error:{_Colors.END} {msg}")

def log_warn(msg: str):
    print(f"{_Colors.YELLOW}Magik Text Save Warning:{_Colors.END} {msg}")


# ============================================================================
# FAST TOKEN PARSER (same behavior as Magik Image Save)
# ============================================================================

class FastTokens:
    """Lightweight token parser"""

    def __init__(self):
        self.tokens = {
            '[time]': str(int(time.time())),
        }
        self._hostname: Optional[str] = None
        self._user: Optional[str] = None

    @property
    def hostname(self) -> str:
        if self._hostname is None:
            import socket
            self._hostname = socket.gethostname()
        return self._hostname

    @property
    def user(self) -> str:
        if self._user is None:
            try:
                self._user = os.getlogin() or 'null'
            except Exception:
                self._user = 'null'
        return self._user

    def parse(self, text: str) -> str:
        """Parse tokens in text"""
        if '[time]' in text:
            text = text.replace('[time]', self.tokens['[time]'])

        if '[time(' in text:
            import time as time_mod
            def _repl(m):
                fmt = m.group(1)
                return time_mod.strftime(fmt, time_mod.localtime())
            text = re.sub(r'\[time\((.*?)\)\]', _repl, text)

        if '[hostname]' in text:
            text = text.replace('[hostname]', self.hostname)

        if '[user]' in text:
            text = text.replace('[user]', self.user)

        return text


# ============================================================================
# MAIN NODE CLASS
# ============================================================================

class Magik_Text_Save(io.ComfyNode):
    """
    Standalone text-saving node. Single text input, no batch processing.
    Duplicate filenames are resolved automatically by appending an
    incrementing number.
    """

    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="Magik.TextSave",
            display_name="Magik Text Save \U0001F4DD",
            category="Magik/IO",
            is_output_node=True,
            inputs=[
                io.String.Input("text", default="", multiline=True),
                io.String.Input("output_path", default='[time(%Y-%m-%d)]'),
                io.String.Input("filename", default="ComfyUI"),
                io.Combo.Input("extension", options=['txt', 'json', 'none']),
                io.Boolean.Input("overwrite", default=False),
            ],
            outputs=[
                io.String.Output("text", display_name="text"),
                io.String.Output("files", display_name="files"),
            ],
        )

    @classmethod
    def execute(cls, text, output_path='', filename="ComfyUI", extension='txt', overwrite=False):

        tokens = FastTokens()
        filename = tokens.parse(filename)

        if not output_path or output_path in ('none', '.', ''):
            output_path = DEFAULT_OUTPUT_DIR
        else:
            output_path = tokens.parse(output_path)
            if not os.path.isabs(output_path):
                output_path = os.path.join(DEFAULT_OUTPUT_DIR, output_path)

        output_path = os.path.normpath(output_path)

        try:
            os.makedirs(output_path, exist_ok=True)
        except OSError as e:
            log_err(f"Cannot create directory {output_path}: {e}")
            return io.NodeOutput(text, "", ui=ui.PreviewText(text))

        if extension == 'none':
            file_ext = ''
        else:
            file_ext = f".{extension}"
            if file_ext not in ALLOWED_EXT:
                log_warn(f"Extension '{extension}' not in allowed list, using txt")
                file_ext = ".txt"

        filepath = os.path.join(output_path, f"{filename}{file_ext}")

        if not overwrite:
            # Auto-number on collision: filename[.ext], then filename_1[.ext], filename_2[.ext], ...
            dupe_counter = 1
            while os.path.exists(filepath):
                filepath = os.path.join(output_path, f"{filename}_{dupe_counter}{file_ext}")
                dupe_counter += 1

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(text)
        except OSError as e:
            log_err(f"Failed to save {filepath}: {e}")
            return io.NodeOutput(text, "", ui=ui.PreviewText(text))

        log_msg(f"Saved: {filepath}")

        return io.NodeOutput(text, filepath, ui=ui.PreviewText(text))
