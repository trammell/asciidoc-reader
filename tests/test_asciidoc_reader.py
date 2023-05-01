from os.path import dirname, join
import pytest

import pelican
from pelican.readers import Readers
from pelican.tests.support import get_settings

import asciidoc_reader

CONTENT_PATH = join(dirname(__file__), "test_data")


# If we can't find the asciidoc CLI tool, skip this entire test module
if not asciidoc_reader.found_command():
    pytest.skip("Can't find asciidoc cli command")


def get_page(path, **kwargs):
    readers = Readers(settings=get_settings(**kwargs))
    return readers.read_file(base_path=CONTENT_PATH, path=path)


def test_reader():
    page = get_page(path="article_with_asc_extension.asc")
    assert type(page) is pelican.contents.Page

    assert "The quick brown fox jumped over the lazy dog" in page.content

    assert "author" in page.metadata
    assert "category" in page.metadata
    assert "date" in page.metadata
    assert "tags" in page.metadata
    assert "title" in page.metadata

    assert page.metadata["author"] == 'Author O. Article'
    assert "Pelican" in page.metadata["tags"]
    assert "Seagull" not in page.metadata["tags"]
