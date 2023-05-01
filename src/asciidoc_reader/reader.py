"""Pelican plugin to support asciidoc page entries."""


import functools
import logging
import os
import re
import subprocess
from typing import Dict, List, Any

# from pelican import signals
import pelican
from pelican.readers import BaseReader

logger = logging.getLogger(__name__)

ASCIIDOC_CANDIDATES = ["asciidoc", "asciidoctor"]


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
    return output.stdout.decode(encoding())


@functools.cache
def asciidoc_command() -> str:
    """Return the name of the found asciidoc utility, if any."""
    for cmd in ASCIIDOC_CANDIDATES:
        if len(call([cmd, "--help"])):
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

    def asciidoc_cmd(self):
        """Return the AsciiDoc command to use for rendering."""
        if "ASCIIDOC_CMD" in self.settings:
            return self.settings.get("ASCIIDOC_CMD")
        elif found_command():
            return asciidoc_command()
        else:
            return "echo"

    def read(self, source_path: str):
        """Parse content and metadata of AsciiDoc files."""
        logger.debug("AsciiDocReader: Reading: %s", source_path)
        adcmd = [self.asciidoc_cmd()]
        adcmd += ["--out-file", "-", "--no-header-footer"]
        adcmd += self.settings.get("ASCIIDOC_OPTIONS", [])
        adcmd += [source_path]
        logger.debug(f"AsciiDocReader: constructed command: {adcmd}")
        content = call(adcmd)
        logger.debug(f"AsciiDocReader: Got content: {content:.50}")
        metadata = self._read_metadata(source_path)
        return content, metadata

    def _read_metadata(self, source_path: str) -> Dict[str, Any]:
        """Extrct the AsciiDoc metadata from the source file."""
        metadata: Dict[str, Any] = {}
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
