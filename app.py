"""
Color Picker - BIOSTAT 821 final project.

Color Picker is a Python-based application that allows the user to upload
an image and identify the closest color name (and its corresponding hex code)
by clicking on different points within the image.

Run this app with `python app.py` and
visit http://127.0.0.1:8050/ in your web browser.
"""

from dash import Dash, dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import numpy as np
import plotly.express as px
from PIL import Image
import cv2
import base64
import io
import json

# cv2.namedWindow("image")
# cv2.setMouseCallback("image", get_color)

dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/\
        dash-bootstrap-templates@V1.0.4/dbc.min.css"
app = Dash(__name__, external_stylesheets=[dbc.themes.MINTY, dbc_css])

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
                        dcc.Upload(
                            id="upload-image",
                            children=html.Div(
                                ["Drag and Drop or ", html.A("Select an Image")]  # noqa
                            ),
                            style={
                                "width": "100%",
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
                    ],
                    width={"size": 5},
                ),
                dbc.Col(  # main panel
                    [
                        html.H6(
                            "Your image:",
                            style={"margin": "10px", "textAlign": "center"},
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
    img = stringToRGB(content_string)
    return dcc.Graph(figure=px.imshow(img))
    return html.Div(
        [
            # html.H5(filename),
            # html.H6(datetime.datetime.fromtimestamp(date)),
            # HTML images accept base64 encoded strings in the same format
            # that is supplied by the upload
            html.Img(src=contents, style={"width": "100%", "height": "500px"}),
            # html.Hr(),
            # html.Div("Raw Content"),
            # html.Pre(
            #     contents[0:200] + "...",
            #     style={"whiteSpace": "pre-wrap", "wordBreak": "break-all"},
            # ),
        ]
    )


@app.callback(
    Output("output-image-upload", "children"),
    Input("upload-image", "contents"),
    # State("upload-image", "filename"),
    # State("upload-image", "last_modified"),
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
    return cv2.cvtColor(np.array(image), cv2.COLOR_BGR2RGB)


if __name__ == "__main__":
    app.run_server(debug=True)
