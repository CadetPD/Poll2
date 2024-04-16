from flask import Flask, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import requests
import os

app = Flask(__name__)
uri = os.getenv("DATABASE_URL")  # Pobranie URI z zmiennej środowiskowej
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))  # Updated size for IPv6 compatibility
    user_agent = db.Column(db.String(256))
    country = db.Column(db.String(100))
    city = db.Column(db.String(100))
    first_vote = db.Column(db.String(128))
    second_vote = db.Column(db.String(128))

with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def home():
    error = None
    if request.method == 'POST':
        ip = request.remote_addr
        user_agent = request.user_agent.string
        first_vote = request.form['first_vote']
        second_vote = request.form['second_vote']

        recent_vote = Vote.query.filter(
            Vote.ip_address == ip,
            Vote.timestamp > datetime.utcnow() - timedelta(hours=12)
        ).first()

        if recent_vote:
            error = "Możesz głosować tylko raz na 12 godzin z tego samego adresu IP."
        else:
            token = os.environ.get('IPINFO_TOKEN', '')
            try:
                response = requests.get(f'http://ipinfo.io/{ip}?token={token}')
                response.raise_for_status()
                ip_data = response.json()
                country = ip_data.get('country', 'Unknown')
                city = ip_data.get('city', 'Unknown')
            except requests.RequestException as e:
                error = f'Error retrieving IP information: {e}'
                country = 'Error'
                city = 'Error'

        if not error:
            new_vote = Vote(ip_address=ip, user_agent=user_agent, country=country, city=city,
                            first_vote=first_vote, second_vote=second_vote)
            db.session.add(new_vote)
            db.session.commit()
            return redirect(url_for('thanks'))

    return render_template('home.html', error=error)

@app.route('/thanks')
def thanks():
    return "Thank you for voting!"

if __name__ == '__main__':
    app.run(debug=True)
