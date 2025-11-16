# helpers.py
from flask import render_template

def apology(message, code=400):
    """
    Render message as an apology to user.
    This mirrors CS50's style: render apology.html with top and bottom.
    """
    return render_template("apology.html", top=code, bottom=message), code
