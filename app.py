import json
import os
import requests
import datetime
from flask import Flask
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask_sqlalchemy import SQLAlchemy

API_KEY = '0a23ae03ca4a723c6b3b8427cdb0bc32'

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'
db = SQLAlchemy(app)


class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        city = request.form['city_name'].capitalize()
        data = {
            'q': city,
            'appid': API_KEY,
            'units': 'metric',
        }
        r = requests.get("http://api.openweathermap.org/data/2.5/weather", params=data)
        if r.status_code == 404:
            flash("The city doesn't exist!")
        elif city in [_.name for _ in City.query.all()]:
            flash("The city has already been added to the list!")
        else:
            db.session.add(City(name=city))
            db.session.commit()
        return redirect('/')
    else:
        query = City.query.all()
        cities_info = []
        for city in query:
            data = {
                'q': city.name,
                'appid': API_KEY,
                'units': 'metric',
            }
            r = requests.get("http://api.openweathermap.org/data/2.5/weather", params=data)
            info = json.loads(r.content)
            temp = round(info['main']['temp'])
            state = info['weather'][0]['description']
            hour = (datetime.datetime.utcnow() + datetime.timedelta(seconds=info['timezone'])).hour
            if 0 <= hour <= 4:
                time = 'night'
            elif 13 <= hour <= 16:
                time = 'day'
            else:
                time = 'evening-morning'
            weather_info = {
                'temp': temp,
                'state': state.capitalize(),
                'city': city.name.upper(),
                'city_id': city.id,
                'time': time,
            }
            cities_info.append(weather_info)
        return render_template('index.html', cities=cities_info)


@app.route('/delete/<city_id>', methods=['GET', 'POST'])
def delete(city_id):
    city = City.query.filter_by(id=city_id).first()
    db.session.delete(city)
    db.session.commit()
    return redirect('/')


if __name__ == '__main__':
    app.run()
