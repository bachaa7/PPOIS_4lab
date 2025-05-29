from flask import Flask, render_template, request, redirect, url_for, session
from models import db, Locomotive, Wagon, Train,Station,Passenger,Ticket,User
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from flask import flash, redirect, url_for
from flask_login import login_user, logout_user, login_required
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///train.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()


@app.route('/')
def index():
    #return redirect(url_for('add_locomotive'))
    return render_template('index.html')

@app.route('/add_locomotive', methods=['GET', 'POST'])
def add_locomotive():
    if request.method == 'POST':
        model = request.form['model']
        drive_type = request.form['drive_type']

        new_loco = Locomotive(model=model, drive_type=drive_type)
        db.session.add(new_loco)
        db.session.commit()

        new_train = Train(locomotive_id=new_loco.id)
        db.session.add(new_train)
        db.session.commit()

        return render_template("add_locomotive.html", message=f"Локомотив {model} и поезд с ним успешно добавлены!")

    return render_template('add_locomotive.html')


@app.route('/add_wagons', methods=['GET', 'POST'])
def add_wagons():
    trains = Train.query.filter(Train.locomotive != None).all()

    if request.method == 'POST':
        train_id = request.form.get('train_id')
        count = int(request.form.get('count'))
        for i in range(count):
            wagon_id = request.form.get(f'id_{i}')
            capacity = request.form.get(f'capacity_{i}')
            price = request.form.get(f'price_{i}')
            wagon = Wagon(id=wagon_id, capacity=capacity, ticket_price=price, train_id=train_id)
            db.session.add(wagon)
        db.session.commit()
        return redirect('/trains')

    return render_template('add_wagons.html', trains=trains)


@app.route('/add_stations', methods=['GET', 'POST'])
def add_stations():
    trains = Train.query.all()

    if request.method == 'POST':
        count = int(request.form['count'])
        selected_train_id = int(request.form['train_id'])
        stations = []

        for i in range(count):
            name = request.form[f'name_{i}']
            arr_time = request.form.get(f'arrival_{i}', '')
            dep_time = request.form.get(f'departure_{i}', '')
            stations.append({
                'name': name,
                'arrival': arr_time if arr_time else None,
                'departure': dep_time if dep_time else None,
                'order': i
            })

        for s in stations:
            station = Station(
                name=s['name'],
                arrival_time=s['arrival'],
                departure_time=s['departure'],
                order=s['order'],
                train_id=selected_train_id
            )
            db.session.add(station)

        db.session.commit()
        message = f"Маршрут из {len(stations)} станций добавлен для поезда {selected_train_id}"
        return render_template('add_stations.html', trains=trains, message=message)

    return render_template('add_stations.html', trains=trains)



@app.route('/add_passengers', methods=['GET', 'POST'])
def add_passengers():
    wagons = Wagon.query.all()
    stations = Station.query.all()
    trains = Train.query.all()

    if request.method == 'POST':
        count = int(request.form['count'])
        train_id = int(request.form['train_id'])

        for i in range(count):
            name = request.form[f'name_{i}']
            from_station = request.form[f'from_station_{i}']
            to_station = request.form[f'to_station_{i}']
            wagon_idx = int(request.form[f'wagon_{i}'])

            selected_wagon = wagons[wagon_idx]
            ticket_price = int(selected_wagon.ticket_price)


            passenger = Passenger(name=name)
            db.session.add(passenger)
            db.session.flush()


            ticket = Ticket(
                price=ticket_price,
                wagon_id=selected_wagon.id,
                passenger_id=passenger.id,
                from_station=from_station,
                to_station=to_station
            )
            db.session.add(ticket)

        db.session.commit()
        flash(f'{count} пассажиров успешно добавлены в поезд {train_id}', 'success')
        return redirect(url_for('passengers'))


    wagons_serializable = []
    for wagon in wagons:
        occupied = Ticket.query.filter_by(wagon_id=wagon.id).count()
        wagons_serializable.append({
            'id': wagon.id,
            'capacity': wagon.capacity,
            'ticket_price': wagon.ticket_price,
            'occupied': occupied
        })

    stations_serializable = [{'id': s.id, 'name': s.name} for s in stations]

    return render_template(
        'add_passengers.html',
        wagons=wagons_serializable,
        stations=stations_serializable,
        trains=trains
    )


@app.route('/passengers')
def passengers():
    passengers = Passenger.query.all()
    return render_template('passengers.html', passengers=passengers)


@app.route('/end_trip', methods=['GET', 'POST'])
def end_trip():
    trains = Train.query.all()

    if request.method == 'POST':
        train_id = int(request.form['train_id'])

        # Найти все вагоны поезда
        wagons = Wagon.query.filter_by(train_id=train_id).all()
        wagon_ids = [w.id for w in wagons]

        # Найти все билеты для этих вагонов
        tickets = Ticket.query.filter(Ticket.wagon_id.in_(wagon_ids)).all()
        passenger_ids = [t.passenger_id for t in tickets if t.passenger_id]
        passengers = Passenger.query.filter(Passenger.id.in_(passenger_ids)).all()

        total_passengers = len(passengers)
        total_income = sum(t.price for t in tickets)

        # Очистка: удаляем билеты, пассажиров, вагоны, станции, поезд
        for ticket in tickets:
            db.session.delete(ticket)
        for passenger in passengers:
            db.session.delete(passenger)
        for wagon in wagons:
            db.session.delete(wagon)
        Station.query.filter_by(train_id=train_id).delete()
        Train.query.filter_by(id=train_id).delete()

        db.session.commit()

        return render_template(
            "end_trip_result.html",
            train_id=train_id,
            total_passengers=total_passengers,
            total_income=total_income
        )

    return render_template("end_trip_form.html", trains=trains)



login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))




@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким именем уже существует')
            return redirect(url_for('register'))
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Регистрация прошла успешно! Войдите в систему.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Неверное имя пользователя или пароль')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/trains')
def trains():
    all_trains = Train.query.all()
    return render_template('trains.html', trains=all_trains)

if __name__ == '__main__':
    app.secret_key = 'your_secret_key'  # ← нужен для сессий и flash-сообщений
    app.run(debug=True)
