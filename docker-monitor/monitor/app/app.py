from contextlib import closing

import docker
from docker.errors import DockerException
from flask import Flask, jsonify, render_template

app = Flask(__name__)


def snapshot():
    """List running containers, or report why Docker can't be reached."""
    try:
        with closing(docker.from_env()) as client:
            containers = client.containers.list()
    except DockerException as e:
        return {"error": f"Docker API Error: {e}"}
    return {
        "containers": [
            {"id": c.short_id, "name": c.name, "status": c.status}
            for c in containers
        ]
    }


@app.route("/containers")
def list_containers():
    data = snapshot()
    return jsonify(data), (503 if "error" in data else 200)


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)  # nosec B104
