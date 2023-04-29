"""Pelican plugin to support asciidoc page entries."""


import functools
import logging
import os
import re
import subprocess
import tempfile
from typing import List

# from pelican import signals
import pelican
from pelican.readers import BaseReader

logger = logging.getLogger(__name__)

ASCIIDOC_CANDIDATES = ["asciidoc", "asciidoctor", "asciidoc3"]


def encoding() -> str:
    """Return encoding used to decode shell output in call function."""
    if os.name == "nt":
        from ctypes import cdll

        return "cp" + str(cdll.kernel32.GetOEMCP())
    return "utf-8"


def call(command: List[str]) -> str:
    """Call a CLI command and return the stdout as string."""
    logger.debug("AsciiDocReader: Running: %s", command)
    output = subprocess.run(command, capture_output=True)

    if output.stderr:
        logger.warning("AsciiDocReader: %s", output.stderr)
    return output.stdout


@functools.cache
def asciidoc_command() -> str:
    """Return the name of the found asciidoc utility, if any."""
    for cmd in ASCIIDOC_CANDIDATES:
        if len(call(cmd + " --help")):
            logger.debug("AsciiDocReader: Using command: '%s'", cmd)
            return cmd
    return ""


@functools.cache
def found_command() -> bool:
    """Return True if the asciidoc executable is found, False otherwise."""
    return len(asciidoc_command()) > 0


class AsciiDocReader(BaseReader):
    """Pelican Reader class for AsciiDoc files."""

    enabled = found_command()
    file_extensions = ["asc", "adoc", "asciidoc"]
    default_options = ["--no-header-footer"]

    def read(self, source_path: str):
        """Parse content and metadata of AsciiDoc files."""
        cmd = self._get_cmd()
        content = ""
        if cmd:
            logger.debug("AsciiDocReader: Reading: %s", source_path)
            optlist = (
                self.settings.get("ASCIIDOC_OPTIONS", [])
                + self.default_options
            )
            options = " ".join(optlist)
            # Beware! # Don't use tempfile.NamedTemporaryFile under Windows:
            # https://bugs.python.org/issue14243
            # Also, use mkstemp correctly (Linux and Windows):
            # https://www.logilab.org/blogentry/17873
            fd, temp_name = tempfile.mkstemp()
            content = call(
                '%s %s -o %s "%s"' % (cmd, options, temp_name, source_path)
            )
            with open(temp_name, encoding="utf-8") as f:
                content = f.read()
            os.close(fd)
            os.unlink(temp_name)
        metadata = self._read_metadata(source_path)
        logger.debug(
            "AsciiDocReader: Got content (showing first 50 chars): %s",
            (content[:50] + "...") if len(content) > 50 else content,
        )
        return content, metadata

    def _get_cmd(self):
        """Return the AsciiDoc command to use for rendering."""
        if "ASCIIDOC_CMD" in self.settings:
            return self.settings.get("ASCIIDOC_CMD")
        elif found_command():
            return asciidoc_command()
        else:
            return "echo"

    def _read_metadata(self, source_path: str) -> dict[str]:
        """Parse the AsciiDoc file and return found metadata."""
        metadata = {}
        with open(source_path, encoding="utf-8") as fi:
            prev = ""
            for line in fi.readlines():
                # Parse for doc title.
                if "title" not in metadata.keys():
                    title = ""
                    if line.startswith("= "):
                        title = line[2:].strip()
                    elif line.count("=") == len(prev.strip()):
                        title = prev.strip()
                    if title:
                        metadata["title"] = self.process_metadata(
                            "title", title
                        )

                # Parse for other metadata.
                regexp = re.compile(r"^:\w+:")
                if regexp.search(line):
                    toks = line.split(":", 2)
                    key = toks[1].strip().lower()
                    val = toks[2].strip()
                    metadata[key] = self.process_metadata(key, val)
                prev = line
        logger.debug("AsciiDocReader: Found metadata: %s", metadata)
        return metadata


def add_reader(readers) -> None:
    """Set AsciiDocReader to handle files with asciidoc file extensions."""
    for ext in AsciiDocReader.file_extensions:
        readers.reader_classes[ext] = AsciiDocReader


def register() -> None:
    """Register function add_reader() to run at init."""
    pelican.signals.readers_init.connect(add_reader)
