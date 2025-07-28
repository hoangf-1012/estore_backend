from flask.cli import FlaskGroup
from app import create_app
from app.extensions import db
from flask_migrate import Migrate
from flask_cors import CORS


app = create_app()

migrate = Migrate(app, db)

CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
cli = FlaskGroup(app)

if __name__ == "__main__":
    cli()
