"""
Color Picker - BIOSTAT 821 final project.

Color Picker is a Python-based application that allows the user to upload
an image and identify the closest color name (and its corresponding hex code)
by clicking on different points within the image.

Run this app with `python app.py` and
visit http://127.0.0.1:8050/ in your web browser.
"""

import dash
from dash import Dash, dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import dash_daq as daq
import numpy as np
import plotly.express as px
from PIL import Image
import cv2
import base64
import io
import math
import sqlite3
from os.path import exists

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


dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/\
        dash-bootstrap-templates@V1.0.4/dbc.min.css"
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.MINTY, dbc_css],
    suppress_callback_exceptions=True,
)

app.layout = html.Div(
    [
        html.H2(
            "Color Picker",
            className="bg-primary text-white p-2 \
            mb-2 text-center",
        ),
        dbc.Row(
            [
                dbc.Col(  # sidebar
                    [
                        html.H6(
                            "Upload an image and click anywhere on it to get \
                                information about the selected color!",
                            style={"margin": "10px"},
                        ),
                        html.Hr(),
                        html.H6(
                            "Closest color match:",
                            style={"margin": "10px"},
                        ),
                        html.Div(id="where"),
                    ],
                    width={"size": 5},
                ),
                dbc.Col(  # main panel
                    [
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
                            # Allow multiple files to be uploaded
                            multiple=True,
                        ),
                        html.Div(
                            id="output-image-upload",
                            style={"textAlign": "center"},  # noqa
                        ),
                    ],
                    width={"size": 7},
                ),
            ],
        ),
    ]
)


def parse_contents(contents):
    """Parse uploaded file and return image."""
    global img
    content_type, content_string = contents.split(",")
    imgdata = base64.b64decode(content_string)
    img = Image.open(io.BytesIO(imgdata))
    fig = px.imshow(img)
    fig.update_xaxes(visible=False, showticklabels=False)
    fig.update_yaxes(visible=False, showticklabels=False)
    return dcc.Graph(id="graph", figure=fig)


@app.callback(
    Output("output-image-upload", "children"),
    Input("upload-image", "contents"),
)
def update_output(list_of_contents):
    """Update uploaded image."""
    if list_of_contents is not None:
        children = [parse_contents(c) for c in list_of_contents]
        return children


def stringToRGB(base64_string):
    """Take in base64 string and return cv image."""
    imgdata = base64.b64decode(str(base64_string))
    image = Image.open(io.BytesIO(imgdata))
    return image


@app.callback(Output("where", "children"), Input("graph", "clickData"))
def click(clickData):
    """Return coordinates of point where image is clicked."""
    if not clickData:
        raise dash.exceptions.PreventUpdate
    coordinates = {k: clickData["points"][0][k] for k in ["x", "y"]}
    color_name, r, g, b, hexcode = get_color(img, coordinates)
    rgb = tuple([r, g, b])
    return html.Div(
        [
            daq.ColorPicker(
                id="my-color-picker-1",
                label=color_name,
                value=dict(hex=hexcode),  # noqa
            ),
            html.Div(
                "RGB Values (R, G, B): " + str(rgb),
                style={"textAlign": "center"},  # noqa
            ),
        ],
        style={"margin": "10px"},
    )


def get_color(img, coordinates):
    """Get closest color match to a given point on an image."""
    cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    x = coordinates["x"]
    y = coordinates["y"]
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
        "CREATE TABLE IF NOT EXISTS colors (color_name TEXT PRIMARY KEY, \
            r INT, g INT, b INT, hex TEXT)"
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
    app.run_server(debug=True)
