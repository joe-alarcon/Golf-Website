from app import app, db, login_manager
from flask import request, render_template, flash, redirect, url_for, session
from models import *
from flask_login import current_user, login_user, logout_user, login_required, UserMixin
from forms import *
from werkzeug.urls import url_parse
import re

check_name_regex = lambda input_name: bool(re.fullmatch(r"""[A-Z][a-z]+( [A-Z][a-z]+){1,4}""", input_name))
check_date_regex = lambda input_date: bool(re.fullmatch(r"\d{4}[-]\d{2}[-]\d{2}", input_date))

@app.route('/', methods=['GET', 'POST'])
def home():
    signin_form = signinform()

    if signin_form.validate_on_submit():
        username = signin_form.sigusername.data
        player_object = Players_Table.get_player(username)
        if player_object and player_object.check_password(signin_form.sigpassword.data):
            login_user(player_object)
            flash("Successfully logged in")
            return redirect(f'/{username}')
        elif not player_object:
            flash(f'There is no user with this username: {username}')
            return redirect("/")
        else:
            flash('Incorrect password')

    return render_template('home.html', sform = signin_form)


@app.route('/signup', methods=['GET', 'POST'])
def signuppage():
    signup_form = signupform()

    if signup_form.validate_on_submit():
        name = signup_form.name.data
        #The RegEx below accepts strings of the following form: Albus Percival Wulfric Brian Dumbledore
        if check_name_regex(name):
            username = signup_form.supusername.data
            #Check for unique usernames
            if Players_Table.get_player(username) is None:
                handicap = signup_form.handicap.data
                email = signup_form.email.data
                user_player = Players_Table(name=name, username=username, email=email, password_hash=None, handicap=handicap)
                user_player.set_password(signup_form.suppassword.data)
                db.session.add(user_player)
                db.session.commit()
                flash("Successfully signed up")
                return redirect("/")
            else:
                flash('A player with that username already exists. Please choose another one.')
        else:
            flash("Invalid name format. Valid format: John Doe")
    #In the logic above, the code intentionally avoids redirect() to 'save' the user input == user doesn't have to re write everything
    return render_template('signup.html', form = signup_form)

@login_manager.user_loader
def load_user(u_id):
    return Players_Table.query.get(int(u_id))

@app.route('/<username>', methods=['GET', 'POST'])
@login_required
def userpagefunc(username):
    player_object = Players_Table.get_player(username)
    form_addscore = addscoreform()
    update_handicap = updatehandicap()
    refresh_betsform = refreshbets()
    updatepass_form = updatepassword()

    if form_addscore.validate_on_submit():
        remain = False
        lst_scores = []
        for i in range(1,19):
            entry = eval(f"form_addscore.hole_{i}.data")
            lst_scores.append(entry)
        course_name = form_addscore.addsccoursename.data
        date = form_addscore.addscdate.data
        check_course = check_name_regex(course_name)
        check_date = check_date_regex(date)
        if check_course and check_date:
            player_object.add_score(lst_scores, course_name, date)
            flash("Successfully added score")
            if form_addscore.bet.data:
                dict_str = form_addscore.dictionary.data
                #The RegEx below accepts a string of the form: {'John Doe': 10, 'Jane Doe': -12, 'Albus Percival Wulfric Brian Dumbledore': 5}
                if not bool(re.fullmatch(r"""[{]{1}(('|"){1}([A-Z][a-z]+( [A-Z][a-z]+){1,4})('|"){1}[:]{1} {1}[-]?\d{1,2}){1}([,]{1} {1}('|"){1}([A-Z][a-z]+( [A-Z][a-z]+){1,4})('|"){1}[:]{1} {1}[-]?\d{1,2})*[}]{1}""", dict_str)):
                    remain = True
                    flash("Incorrect Python Dictionary syntax")
                else:
                    try:
                        dictionary = eval(dict_str)
                    except SyntaxError:
                        remain = True
                        flash("Incorrect Python Dictionary syntax")
                    if isinstance(dictionary, dict):
                        statements = player_object.bet_with_other_players(date, course_name, dictionary)
                        flash("Successfully added bets")
                        for statement in statements:
                            flash(statement)
            db.session.commit()
            flash("Committed")

        elif not check_course:
            remain = True
            flash("Invalid course name syntax. Valid: The Old Course")
        elif not check_date:
            remain = True
            flash("Invalid date syntax. Valid: YYYY-MM-DD")

        if not remain:
            return redirect(f"/{username}")

    if update_handicap.validate_on_submit():
        player_object.update_handi(update_handicap.new_handi.data)
        flash("Handicap Updated")
        db.session.commit()
        flash("Committed")
        return redirect(f"/{username}")

    if refresh_betsform.validate_on_submit():
        course_name = refresh_betsform.rbetcoursename.data
        date = refresh_betsform.rbetdate.data
        check_course = check_name_regex(course_name)
        check_date = check_date_regex(date)
        if check_date and check_course:
            player_name = refresh_betsform.rbetplayername.data
            check_player_name = check_name_regex(player_name)
            if check_player_name:
                dictionary = {player_name: refresh_betsform.rbetstrokes.data}
                statements = player_object.bet_with_other_players(date, course_name, dictionary)
                for statement in statements:
                    flash(statement)
                db.session.commit()
                flash("Committed")
                return redirect(f"/{username}")

    if updatepass_form.validate_on_submit():
        player_object.set_password(updatepass_form.newpassword.data)
        flash("Updated password")
        db.session.commit()
        flash("Committed")
        return redirect(f"/{username}")

    return render_template('userpage.html', player=player_object, addsc=form_addscore, update_handi=update_handicap, refresh_bets=refresh_betsform, passform=updatepass_form)

@app.route('/<username>/bet<id>')
@login_required
def see_bet(username, id):
    bet_object = Bets_Table.get_bet(id)
    return render_template('fullbet.html', bet=bet_object, username=username)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have logged out.')
    return redirect('/')


@login_manager.unauthorized_handler
def unauthorized():
    flash('Unauthorized')
    return redirect("/")



#Space
