# -*- coding: utf-8 -*-

from flask import render_template

from kharcha import app


@app.route('/settlements/')
def settlements():
    return render_template('baseframe/message.html', message="Coming soon")
