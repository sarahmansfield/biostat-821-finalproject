"""
Color Matcher - BIOSTAT 821 final project.

Color Matcher is a Python-based application that allows the user to upload
an image and identify the closest color and its corresponding information
(hex code, RGB values, etc) by clicking on different points within the image.

Run this app with `python app.py` and
visit http://127.0.0.1:8050/ in your web browser.
"""

import dash
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import dash_daq as daq
import numpy as np
import plotly.express as px
from PIL import Image, UnidentifiedImageError
import cv2
import base64
import io
import math
import sqlite3
from os.path import exists
from typing import Tuple, Any

# additional trace of transparent points that are scattered
# uniformly across the figure
# we need this so that we can use clickData callback to
# determine clicked coordinates
GS = 100
fig = px.line(
    x=np.linspace(0, 1, 300),
    y=(np.sin(np.linspace(0, math.pi * 3, 300)) / 2) + 0.5,  # noqa
).add_traces(
    px.scatter(
        x=np.repeat(np.linspace(0, 1, GS), GS),
        y=np.tile(np.linspace(0, 1, GS), GS),  # noqa
    )
    .update_traces(marker_color="rgba(0,0,0,0)")
    .data
)
# global image - we want to be able to access the image across functions
img = np.zeros([100, 100, 3], dtype=np.uint8)
img.fill(255)
img = Image.fromarray(img)


dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/\
        dash-bootstrap-templates@V1.0.4/dbc.min.css"
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.JOURNAL, dbc_css],
    suppress_callback_exceptions=True,
)

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(
            dbc.NavLink(
                "GitHub",
                href="https://github.com/sarahmansfield",
            )
        ),
        dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem("More pages", header=True),
                dbc.DropdownMenuItem("Dash", href="https://dash.plotly.com/"),
                dbc.DropdownMenuItem(
                    "Source Code",
                    href="https://github.com/sarahmansfield/biostat-821-finalproject",  # noqa
                ),
            ],
            nav=True,
            in_navbar=True,
            label="More",
        ),
    ],
    brand="COLOR MATCHER",
    color="primary",
    dark=True,
)

app.layout = html.Div(
    [
        navbar,
        dbc.Row(
            [
                dbc.Col(  # sidebar
                    [
                        dbc.Card(
                            [
                                dbc.CardImg(
                                    src="/static/header.jpg",
                                    top=True,
                                ),
                                dbc.CardBody(
                                    [
                                        html.H6(
                                            "Closest color match:",
                                            className="card-title",
                                        ),
                                        html.Div(id="colormatch"),
                                    ]
                                ),
                            ],
                            style={"margin": "10px"},
                        ),
                    ],
                    width={"size": 5},
                ),
                dbc.Col(  # main panel
                    [
                        html.H5(
                            "Upload an image and click anywhere on it to get \
                                 information about the selected color!",
                            style={"margin": "10px", "textAlign": "center"},
                        ),
                        dcc.Upload(
                            id="upload-image",
                            children=html.Div(
                                ["Drag and Drop or ", html.A("Select an Image")]  # noqa
                            ),
                            style={
                                "width": "97%",
                                "height": "60px",
                                "lineHeight": "60px",
                                "borderWidth": "1px",
                                "borderStyle": "dashed",
                                "borderRadius": "5px",
                                "textAlign": "center",
                                "margin": "10px",
                            },
                        ),
                        dbc.Spinner(
                            html.Div(
                                id="output-image-upload",
                                style={"textAlign": "center"},  # noqa
                            ),
                            color="primary",
                        ),
                    ],
                    width={"size": 7},
                ),
            ],
        ),
    ]
)


def parse_contents(contents: str) -> html.Div:
    """Parse uploaded image file and return image."""
    global img
    content_type, content_string = contents.split(",")
    imgdata = base64.b64decode(content_string)
    try:
        img = Image.open(io.BytesIO(imgdata))
    except UnidentifiedImageError:
        return dbc.Alert(
            "Invalid file! Please upload a valid image file.",
            color="danger",
            dismissable=True,
            style={"width": "97%", "margin": "10px"},
        )
    fig = px.imshow(img)
    fig.update_xaxes(visible=False, showticklabels=False)
    fig.update_yaxes(visible=False, showticklabels=False)
    return dcc.Graph(id="graph", figure=fig)


@app.callback(
    Output("output-image-upload", "children"),
    Input("upload-image", "contents"),
)
def update_output(contents: str) -> html.Div:
    """Update uploaded image."""
    if contents is not None:
        children = parse_contents(contents)
        return children


@app.callback(Output("colormatch", "children"), Input("graph", "clickData"))
def click(clickData: dict[str, list[dict[str, Any]]]) -> html.Div:
    """Return colorpicker element with information about color match \
        corresponding to point where image is clicked."""
    if not clickData:
        raise dash.exceptions.PreventUpdate
    coordinates = {k: clickData["points"][0][k] for k in ["x", "y"]}
    color_name, r, g, b, hexcode = get_color(img, coordinates)
    return html.Div(
        [
            daq.ColorPicker(
                id="colorpicker",
                label=color_name,
                value=dict(hex=hexcode),  # noqa
            ),
        ],
        style={"margin": "10px"},
    )


def get_color(
    img: Image, coordinates: dict[str, int]
) -> Tuple[str, int, int, int, str]:
    """Return color name, RGB values, and hex code of the closest \
        color match to a given point on an image."""
    cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    bounds = cv_img.shape
    x = coordinates["x"]
    y = coordinates["y"]
    if y > bounds[0] or x > bounds[1]:
        raise IndexError("Index is out of bounds")
    b, g, r = cv_img[y, x]
    b = int(b)
    g = int(g)
    r = int(r)

    con = sqlite3.connect("data/color_data.db")
    cur = con.cursor()
    cur.execute("SELECT * FROM colors")
    colors = cur.fetchall()
    con.close()

    min = np.inf
    for color_name, r_val, g_val, b_val, hexcode in colors:
        diff = abs(r - r_val) + abs(g - g_val) + abs(b - b_val)
        if diff <= min:
            color_match = color_name
            hex_match = hexcode
            r_match = r_val
            g_match = g_val
            b_match = b_val
            min = diff
    return color_match, r_match, g_match, b_match, hex_match


def parse_data(filename: str) -> None:
    """Read and parse the color data file and insert the data into \
        a SQLite database."""
    try:
        lines = open(filename, encoding="utf-8-sig").readlines()
    except FileNotFoundError:
        raise
    lines = lines[60:]
    con = sqlite3.connect("data/color_data.db")
    cur = con.cursor()
    # create and populate data table
    cur.execute(
        "CREATE TABLE IF NOT EXISTS colors (color_name TEXT, \
            r INT, g INT, b INT, hex TEXT PRIMARY KEY)"
    )
    for line in lines:
        vals = line.split()[1:8]
        color = vals[0]
        r, g, b = map(int, vals[2:5])
        hexcode = vals[6]
        cur.execute(
            "INSERT OR IGNORE INTO colors VALUES \
                (?, ?, ?, ?, ?)",
            [color, r, g, b, hexcode],
        )
    con.commit()
    con.close()


if __name__ == "__main__":
    if not exists("data/color_data.db"):
        parse_data("data/color.names.txt")
    app.run_server(debug=False)
