"""Test color matcher app functions."""

import pytest
import sqlite3
from os.path import exists
from app import parse_data, parse_contents, get_color
from dash import dcc
import dash_bootstrap_components as dbc
import base64
from PIL import Image
import io


def test_parse_data():
    """Test parse_data()."""
    if not exists("data/color_data.db"):
        parse_data("tests/colortestdata.txt")
    con = sqlite3.connect("data/color_data.db")
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    assert [table[0] for table in cur.fetchall()] == ["colors"]
    cur.execute("SELECT * FROM colors")
    rows = cur.fetchall()
    assert len(rows) == 10
    assert len(rows[0]) == 5
    con.close()


def test_bad_parse_data():
    """Test invalid input handling for parse_data()."""
    with pytest.raises(FileNotFoundError) as excinfo:
        parse_data("no file here")
    assert "No such file or directory" in str(excinfo.value)


def test_parse_contents():
    """Test parse_contents()."""
    file = open("tests/test-image.jpg", "rb").read()
    file_contents = "content_type," + base64.b64encode(file).decode()
    assert isinstance(parse_contents(file_contents), dcc.Graph)


def test_bad_parse_contents():
    """Test invalid input handling for parse_contents()."""
    file = open("tests/test-image.pdf", "rb").read()
    invalid_file = "content_type," + base64.b64encode(file).decode()
    assert isinstance(parse_contents(invalid_file), dbc.Alert)


def test_get_color():
    """Test get_color()."""
    file = open("tests/test-image.jpg", "rb").read()
    img = Image.open(io.BytesIO(file))
    assert get_color(img, {"x": 981, "y": 179}) == (
        "color5",
        155,
        255,
        255,
        "#9BFFFF",
    )  # noqa
    assert get_color(img, {"x": 976, "y": 995}) == (
        "color7",
        243,
        223,
        178,
        "#F3DFB2",
    )  # noqa


def test_bad_get_color():
    """Test invalid input handling for get_color()."""
    file = open("tests/test-image.jpg", "rb").read()
    img = Image.open(io.BytesIO(file))
    with pytest.raises(IndexError) as excinfo1:
        get_color(img, {"x": 98100, "y": 179})
    assert "Index is out of bounds" in str(excinfo1.value)
    with pytest.raises(IndexError) as excinfo2:
        get_color(img, {"x": 981, "y": 17900})
    assert "Index is out of bounds" in str(excinfo2.value)
