from flask import Flask, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from detectvpn import detect
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///votes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(15))
    user_agent = db.Column(db.String(256))
    first_vote = db.Column(db.String(128))
    second_vote = db.Column(db.String(128))
    vpn_status = db.Column(db.String(50))

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

        # Ograniczenie czasowe głosowania z tego samego IP
        recent_vote = Vote.query.filter(Vote.ip_address == ip, Vote.timestamp > datetime.utcnow() - timedelta(hours=12)).first()
        if recent_vote:
            error = "Możesz głosować tylko raz na 12 godzin z tego samego adresu IP."
        else:
            # Sprawdzenie VPN
            vpn_check = detect.ip(ip)
            new_vote = Vote(ip_address=ip, user_agent=user_agent, first_vote=first_vote, second_vote=second_vote, vpn_status=vpn_check)
            db.session.add(new_vote)
            db.session.commit()
            return redirect(url_for('thanks'))

    return render_template('home.html', error=error)

@app.route('/thanks')
def thanks():
    return "Dziękujemy za oddanie głosu!"

if __name__ == '__main__':
    app.run(debug=True)
