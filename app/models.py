from . import db # Import db from the current package (app)
from datetime import datetime

class PotentialLocation(db.Model):
    __tablename__ = 'potential_locations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(300), nullable=True) # Full address
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    # Data from reference point (e.g., family's address)
    # These would be specific to a user or a reference search
    # For a multi-user system, these might go into a different table linking users to locations
    # For this MVP, we assume a single reference point context for simplicity
    reference_address = db.Column(db.String(300), nullable=True) # The address used for filtering
    driving_time_seconds = db.Column(db.Integer, nullable=True) # Driving time from reference_address
    driving_time_text = db.Column(db.String(50), nullable=True) # e.g., "1 hour 15 mins"

    # General notes / future enrichment
    population = db.Column(db.Integer, nullable=True)
    wikipedia_url = db.Column(db.String(300), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<PotentialLocation {self.name}>'

    def to_dict(self):
        """Serializes the object to a dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'reference_address': self.reference_address,
            'driving_time_seconds': self.driving_time_seconds,
            'driving_time_text': self.driving_time_text,
            'population': self.population,
            'wikipedia_url': self.wikipedia_url,
            'notes': self.notes,
            'date_added': self.date_added.isoformat() if self.date_added else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
        }
