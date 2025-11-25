"""
Terminal plugin for Siklu EH devices.
"""

import re
from ansible_collections.ansible.netcommon.plugins.plugin_utils.terminal_base import TerminalBase


class TerminalModule(TerminalBase):
    """
    Terminal plugin for Siklu EH CLI interaction.
    """

    # Prompt pattern: minimum 2 characters before '>', excluding special chars
    # Format: hostname> where hostname contains only allowed characters
    terminal_stdout_re = [
        re.compile(rb"[\r\n]?[^%<>&#'/\\\"|{};,\s]{2,}>\s?$"),
    ]

    # Error patterns - TODO: verify with real device output
    terminal_stderr_re = [
        re.compile(rb"% ?Error", re.I),
        re.compile(rb"% ?Bad secret", re.I),
        re.compile(rb"invalid input", re.I),
        re.compile(rb"connection timed out", re.I),
    ]

    def on_open_shell(self) -> None:
        """
        Called when shell is opened.

        Siklu EH doesn't support terminal length/width commands.
        Pagination is not implemented in the device.
        """
        pass
