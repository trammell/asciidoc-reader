import os

import pelican
import pytest
from pelican.readers import Readers
from pelican.tests.support import get_settings

import asciidoc_reader

# If we can't find the asciidoc CLI tool, skip this entire test module
if not asciidoc_reader.found_command():
    pytest.skip("Can't find asciidoc cli command")


def get_page(path, **kwargs):
    test_data = os.path.join(os.path.dirname(__file__), "test_data")
    readers = Readers(settings=get_settings(**kwargs))
    return readers.read_file(base_path=test_data, path=path)


def test_reader():
    page = get_page(path="article_with_asc_extension.asc")
    assert type(page) is pelican.contents.Page

    assert "The quick brown fox jumped over the lazy dog" in page.content

    assert "author" in page.metadata
    assert "category" in page.metadata
    assert "date" in page.metadata
    assert "tags" in page.metadata
    assert "title" in page.metadata

    assert page.metadata["author"] == "Author O. Article"
    assert "Pelican" in page.metadata["tags"]
    assert "Seagull" not in page.metadata["tags"]
