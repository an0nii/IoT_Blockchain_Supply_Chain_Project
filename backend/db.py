from flask import Blueprint, jsonify, request
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Device(db.Model):
	__tablename__ = "devices"
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	name = db.Column(db.String(100), nullable=False)
	type = db.Column(db.String(50), nullable=False)
	address = db.Column(db.String(42), nullable=False, unique=True)
	description = db.Column(db.Text, nullable=True)

	def as_dict(self):
		return {
			"id": self.id,
			"name": self.name,
			"type": self.type,
			"address": self.address,
			"description": self.description
		}


def init_db(app):
	app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://iotadmin:password@localhost:5432/iotdata"
	app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

	db.init_app(app)
	with app.app_context():
		db.create_all()


devices_bp = Blueprint("devices", __name__)


@devices_bp.route("/devices", methods=["GET"])
def get_devices():
	try:
		devices = Device.query.all()
		return jsonify({"devices": [d.as_dict() for d in devices]})
	except Exception as e:
		return jsonify({"error": str(e)}), 500


@devices_bp.route("/devices", methods=["POST"])
def create_device():
	try:
		data = request.json
		existing = Device.query.filter_by(address=data.get("address")).first()
		if existing:
			return jsonify({"device": existing.as_dict(), "message": "Device already exists."}), 200

		new_device = Device(
			name=data.get("name"),
			type=data.get("type"),
			address=data.get("address"),
			description=data.get("description")
		)
		db.session.add(new_device)
		db.session.commit()
		return jsonify({"device": new_device.as_dict()}), 201
	except Exception as e:
		return jsonify({"error": str(e)}), 500
