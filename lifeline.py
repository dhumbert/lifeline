import dateutil.parser
from functools import partial
from datetime import date
from flask import Flask, render_template, redirect, request, session, url_for, flash
from flask.ext.login import LoginManager, login_required, login_user, logout_user, current_user
import model
import settings

# google api
from oauth2client.client import OAuth2WebServerFlow


app = Flask(__name__)
app.secret_key = settings.SESSION_SECRET_KEY
login = LoginManager()
login.init_app(app)
login.login_view = "login"

@login.user_loader
def load_user(id):
    return model.get_user(id)


@app.route('/')
@login_required
def today():
    dateToday = date.today()
    return date_view(dateToday.year, dateToday.month, dateToday.day)


@app.route('/<int:year>/<int:month>/<int:day>')
@login_required
def date_view(year, month, day):
    currentDate = dateutil.parser.parse("{}-{}-{}".format(year, month, day), yearfirst=True).date()

    dayObj = model.Day(currentDate)

    date_pagination = dayObj.get_date_pagination(partial(url_for, 'date_view'))
    notes = dayObj.get_notes(current_user._get_current_object())
    try:
        events = dayObj.get_events(current_user._get_current_object())
    except:
        return redirect(url_for('google_auth'))


    data_template = dayObj.get_data_template(render_template)

    return render_template('day.html',
                           data_template=data_template,
                           day=dayObj,
                           notes=notes, events=events,
                           date_pagination=date_pagination,
                           moods=settings.MOODS)


@app.route('/google-auth')
@login_required
def google_auth():
    # change redirect uri: https://console.developers.google.com/project/667824890122/apiui/credential
    flow = OAuth2WebServerFlow(
        client_id=settings.GOOGLE_API_CLIENT_ID,
        client_secret=settings.GOOGLE_API_CLIENT_SECRET,
        scope='https://www.googleapis.com/auth/calendar',
        redirect_uri=settings.BASE_URL + "google-auth-callback",
        access_type='offline',
        approval_prompt='force',
        user_agent='LifeLine/1.0')

    auth_uri = flow.step1_get_authorize_url()
    return redirect(auth_uri)


@app.route('/google-auth-callback')
@login_required
def google_auth_callback():
    code = request.args.get('code')
    if code:
        # exchange the authorization code for user credentials
        flow = OAuth2WebServerFlow(settings.GOOGLE_API_CLIENT_ID,
                                   settings.GOOGLE_API_CLIENT_SECRET,
                                   "https://www.googleapis.com/auth/calendar")
        flow.redirect_uri = request.base_url
        credentials = flow.step2_exchange(code)

        current_user.tokens['gcal'] = credentials.to_json()
        current_user.save()

    return redirect(url_for('today'))


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = model.authenticate(request.form['username'], request.form['password'])
        if user:
            login_user(user)
            url = request.form['next'] if 'next' in request.form else '/'
            return redirect(url)
        else:
            flash('Invalid login', 'error')
            return redirect('/login')
    return render_template('login.html', next=request.args.get('next'))


@app.route("/logout")
def logout():
    logout_user()
    return redirect('/login')


@app.route('/ajax/save', methods=['POST'])
@login_required
def ajax_save():
    model.Day(request.form['date']).save(current_user, dict(request.form))
    return "true"


@app.route('/ajax/save-mood', methods=['POST'])
@login_required
def ajax_save_mood():
    model.Day(request.form['date']).save_mood(current_user, dict(request.form))
    return "true"


if __name__ == '__main__':
    app.run(debug=True)
