from flask import Flask, render_template, jsonify, request
from routes import register_blueprints

app = Flask(__name__)


register_blueprints(app)


if __name__ == "__main__":
    app.run(debug=True)