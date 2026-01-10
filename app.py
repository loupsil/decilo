from flask import Flask, send_from_directory, Response, render_template, redirect, jsonify, request
from dotenv import load_dotenv
import os
from decilo import decilo_bp
from ear_impressions import ear_impressions_bp

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Register blueprints
app.register_blueprint(decilo_bp)
app.register_blueprint(ear_impressions_bp)

@app.route('/')
def index():
    return render_template('decilo.html', is_portal=True)

@app.route('/decilo')
def decilo():
    return render_template('decilo.html', is_portal=True)

@app.route('/ear-impressions')
def ear_impressions():
    return render_template('ear_impressions.html')

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=8000)
