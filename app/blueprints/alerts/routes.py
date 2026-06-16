from flask import Blueprint, render_template, jsonify
from app.blueprints.landing import landing_bp

@landing_bp.route('/')
def index():
    return jsonify({'message': 'Placeholder'})
