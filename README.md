# Color Matcher

Color Matcher is a Python-based application that allows the user to upload an image and identify the closest color and its corresponding information (hex code, RGB values, etc) by clicking on different points within the image.

### Setup/Installation

To run the application, first clone the repository by typing the following command in the terminal:
```python
>> git clone https://github.com/sarahmansfield/biostat-821-finalproject.git
```
Once cloned and navigated to the correct directory, run the app by typing 
```python
>> python app.py
```
in your terminal and
visit http://127.0.0.1:8050/ in your web browser.

## Contributors

To add function tests, contributors may modify the `test_app.py` file.
To run a test session, type the following command in the terminal:
```python
>> pytest test_app.py
```

## Architecture

This application is built using the [Dash](https://plotly.com/dash/) framework, and utilizes a SQLite database for storing and retrieving color data. The color data used in this app was sourced from [Martin Krzywinski](http://mkweb.bcgsc.ca/)'s compiled [list of color names](http://mkweb.bcgsc.ca/colornames/).
