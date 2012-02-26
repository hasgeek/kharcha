# -*- coding: utf-8 -*-

from flask import render_template
from kharcha import app


@app.route('/receipts')
def receipts():
    # Gallery of receipts
    return render_template('baseframe/message.html', message="Coming soon")


@app.route('/receipts/new')
def receipt_new():
    return render_template('baseframe/message.html', message="Coming soon")
