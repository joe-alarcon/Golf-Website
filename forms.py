from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, RadioField, PasswordField, IntegerField, FloatField
from wtforms.validators import DataRequired, Email, EqualTo

class signinform(FlaskForm):
    sigusername = StringField('Username', validators=[DataRequired()])
    sigpassword = PasswordField('Password', validators=[DataRequired()])
    sigsubmit = SubmitField('Submit')

class signupform(FlaskForm):
    name = StringField('Name - format: John Doe', validators=[DataRequired()])
    supusername = StringField('Username', validators=[DataRequired()])
    handicap = FloatField('Handicap - must be a decimal number: 10.4', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    suppassword = PasswordField('Password', validators=[DataRequired()])
    supsubmit = SubmitField('Submit')

class addscoreform(FlaskForm):
    addsccoursename = StringField('Course Name', validators=[DataRequired()])
    addscdate = StringField('Date', validators=[DataRequired()])
    hole_1 = IntegerField('Hole 1', validators=[DataRequired()])
    hole_2 = IntegerField('Hole 2', validators=[DataRequired()])
    hole_3 = IntegerField('Hole 3', validators=[DataRequired()])
    hole_4 = IntegerField('Hole 4', validators=[DataRequired()])
    hole_5 = IntegerField('Hole 5', validators=[DataRequired()])
    hole_6 = IntegerField('Hole 6', validators=[DataRequired()])
    hole_7 = IntegerField('Hole 7', validators=[DataRequired()])
    hole_8 = IntegerField('Hole 8', validators=[DataRequired()])
    hole_9 = IntegerField('Hole 9', validators=[DataRequired()])
    hole_10 = IntegerField('Hole 10', validators=[DataRequired()])
    hole_11 = IntegerField('Hole 11', validators=[DataRequired()])
    hole_12 = IntegerField('Hole 12', validators=[DataRequired()])
    hole_13 = IntegerField('Hole 13', validators=[DataRequired()])
    hole_14 = IntegerField('Hole 14', validators=[DataRequired()])
    hole_15 = IntegerField('Hole 15', validators=[DataRequired()])
    hole_16 = IntegerField('Hole 16', validators=[DataRequired()])
    hole_17 = IntegerField('Hole 17', validators=[DataRequired()])
    hole_18 = IntegerField('Hole 18', validators=[DataRequired()])
    bet = BooleanField('Played with bets')
    dictionary = StringField('{playername1: strokes, ... playernamen: strokes}')
    addscsubmit = SubmitField('Submit')

class betinformationform(FlaskForm):
    betplayername = StringField("What is the player's name?")
    betstrokes = IntegerField('How many strokes exchanged?')
    betsubmit = SubmitField('Submit')

class updatehandicap(FlaskForm):
    new_handi = FloatField("Updated handicap", validators=[DataRequired()])
    uphandisubmit = SubmitField('Submit')

class refreshbets(FlaskForm):
    refresh = BooleanField('Is the betting scheme not complete? Click here, enter the info, and submit: ', validators=[DataRequired()])
    rbetcoursename = StringField('Course Name', validators=[DataRequired()])
    rbetdate = StringField('Date', validators=[DataRequired()])
    rbetplayername = StringField('Player Name', validators=[DataRequired()])
    rbetstrokes = IntegerField('Strokes Exchanged', validators=[DataRequired()])
    rbetsubmit = SubmitField('Submit')

class updatepassword(FlaskForm):
    newpassword = PasswordField('New Password', validators=[DataRequired()])
    passubmit = SubmitField('Submit')

#Space
