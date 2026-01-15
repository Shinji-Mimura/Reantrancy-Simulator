"""
Flask Backend for Reentrancy Attack Examples
Serves API endpoints for the Svelte frontend.
"""

from flask import Flask, jsonify
from flask_cors import CORS
from examples import get_all_examples, get_example_by_id

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes


@app.route("/api/examples", methods=["GET"])
def list_examples():
    """Return all examples with basic info."""
    examples = get_all_examples()
    # Return summary info for listing
    return jsonify([
        {
            "id": ex["id"],
            "title": ex["title"],
            "subtitle": ex["subtitle"],
            "description": ex["description"][:200] + "..."
        }
        for ex in examples
    ])


@app.route("/api/examples/<example_id>", methods=["GET"])
def get_example(example_id):
    """Return full details for a specific example."""
    example = get_example_by_id(example_id)
    if example is None:
        return jsonify({"error": "Example not found"}), 404
    return jsonify(example)


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
