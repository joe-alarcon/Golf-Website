from app import db, login_manager
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

def parse_iter_ent_to_str(iterable):
    return list(map(lambda x: str(x), iterable))

class Players_Table(UserMixin, db.Model):
    __tablename__ = "Player Users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), unique = True, index = True)
    password_hash = db.Column(db.String(128))
    handicap = db.Column(db.Float)
    joined_at = db.Column(db.DateTime(), default = datetime.utcnow)
    scores = db.relationship("Scores_Table", back_populates="player", lazy='subquery', cascade='all, delete-orphan')
    bets = db.relationship("Bets_Table", back_populates="player", lazy='subquery', cascade='all, delete-orphan')

    def __repr__(self):
        return '<Player {} with handicap {}.>'.format(self.name, self.handicap)

    @staticmethod
    def get_player(i_username):
        return Players_Table.query.filter_by(username=i_username).first()

    @staticmethod
    def get_player_by_name(i_name):
        return Players_Table.query.filter_by(name=i_name).first()

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_score(self, date, i=None, object=False):
        s = None
        for score in self.scores:
            if score.date == date:
                s = score
        if s is None:
            return None
        if object:
            return s
        if isinstance(i, int):
            return s.get(i)
        else:
            return s.get()

    def update_handi(self, update):
        self.handicap = update

    def add_score(self, score_lst, course_name, idate):
        course = Courses_Table.get_course(course_name)
        score_object = Scores_Table.create_score(self.name, score_lst, course_name, course.course_par, idate)
        self.scores.append(score_object)


    def bet_with_other_players(self, date, course_name, dictionary_of_strokes_exchanges):
        """
        This function calculates the bets of self with all other players
        who played on date at course. Returns a list of strings with statements
        that contain information on who self played against and results, and appends
        the bets made to each player's bets list.
        """
        def pressures(self_score, other_score):
            """
            Helper function that keeps track and returns the pressures
            """
            def calculation(current_p_lst, start, self_score, other_score):
                """
                Helper function that calculates each pressure history based on score
                """
                current_value_of_pressure = 0
                check = True
                for i in range(start):
                    current_p_lst.append(0)
                for i in range(start, 9):
                    if self_score[i] < other_score[i]:
                        current_value_of_pressure += 1
                    elif self_score[i] > other_score[i]:
                        current_value_of_pressure -= 1
                    current_p_lst.append(current_value_of_pressure)
                    if current_value_of_pressure == 2 and check:
                        end = i+1
                        check = False
                if check:
                    end = 9
                return end, current_value_of_pressure

            #Front 9
            self_score_front = self_score[:9]
            other_score_front = other_score[:9]
            front9 = []
            list1a = []
            list2a = []
            list3a = []
            list4a = []
            list5a = []
            start = 0
            for num in range(1,6):
                start, pressure = calculation(eval(f"list{num}a"), start, self_score_front, other_score_front)
                front9.append(pressure)
            #Back 9
            self_score_back = self_score[9:]
            other_score_back = other_score[9:]
            back9 = []
            list1b = []
            list2b = []
            list3b = []
            list4b = []
            list5b = []
            start = 0
            for num in range(1,6):
                start, pressure = calculation(eval(f"list{num}b"), start, self_score_back, other_score_back)
                back9.append(pressure)
            #Final stats
            pressures_tuple = (front9, back9)
            total_pressures = 0
            for row_pressure in pressures_tuple:
                for pressure in row_pressure:
                    if pressure < 0:
                        total_pressures -= 1
                    elif pressure > 0:
                        total_pressures += 1
            match = front9[0] + back9[0]
            all_pressures = {"front9": [list1a, list2a, list3a, list4a, list5a], "back9": [list1b, list2b, list3b, list4b, list5b]}
            return all_pressures, total_pressures, match

        def handicap_adjust(score, handidiff, course):
            def helper(diff):
                hole = course.get_hole_from_diff(diff+1)
                score[hole] -= 1

            for i in range(handidiff):
                hole_diff = i % 18
                helper(hole_diff)


        def convert(all_pressures, total_pressures, match):
            def negative_mapping(lst):
                return list(map(lambda x: -x, lst))

            new_front = []
            front = all_pressures["front9"]
            for lst in front:
                new_front.append(negative_mapping(lst))
            new_back = []
            back = all_pressures["back9"]
            for lst in back:
                new_back.append(negative_mapping(lst))
            new_all_ps = {"front9": new_front, "back9": new_back}
            new_tot_p = -total_pressures
            new_match = -match
            return new_all_ps, new_tot_p, new_match

        def check_if_played(player, date, course_name):
            score_object = player.get_score(date, object=True)
            if score_object is None:
                return f"{player.name} did not play on {date}."
            if score_object.course_name != course_name:
                return f"{player.name} did not play at {course_name} on {date}."
            return score_object

        def num_score_units(score_lst, course):
            unit = 0
            par = course.get_par()
            for i in range(0,18):
                if score_lst[i] < par[i]:
                    unit += 1
            return unit

        def pressure_str_func(front9, back9):
            lst = []
            for f_lst, b_lst in zip(front9, back9):
                pressure_lst_str = " ".join(parse_iter_ent_to_str(f_lst)) + " | " + " ".join(parse_iter_ent_to_str(b_lst))
                lst.append(pressure_lst_str)
            return lst

        front9_str = " ".join(parse_iter_ent_to_str(range(1,10))) + " | "
        back9_str = " ".join(parse_iter_ent_to_str(range(10,19)))
        hole_str = front9_str + back9_str
        #Start of bet_with_other_players
        #Getting self score and checks if self played on date and course
        course_object = Courses_Table.get_course(course_name)
        return_statements = []
        self_score = check_if_played(self, date, course_name)
        if isinstance(self_score, str):
            return self_score
        self_score_lst = self_score.get()[:]
        #Players whose bet has already been calculated with self (on date)
        recorded_players = [bet.get_player() for bet in self.bets if bet.date == date]
        #Units made by self
        self_units = num_score_units(self_score_lst, course_object)
        #Bet for all players who are not in recorded_players
        for player_name in dictionary_of_strokes_exchanges.keys():
            player = Players_Table.get_player_by_name(player_name)
            #Player does not play against themselves; if bet is already calculated, skip; if player is not found, skip
            if player_name in recorded_players:
                return_statements.append(f"{player.name} already has bet against {self.name}.")
                continue
            if player.id == self.id:
                continue
            if player is None:
                return_statements.append(f"There is no player with name {player_name}.")
                continue
            #Player Strokes - or, if player did not play on date and course, skip
            other_score = check_if_played(player, date, course_name)
            if isinstance(other_score, str):
                return_statements.append(other_score)
                continue
            other_score_lst = other_score.get()[:]
            #Player units & Calculate net units
            other_units = num_score_units(other_score_lst, course_object)
            units = self_units - other_units
            #Adjusting the score of self or players for Handicap based on strokes given
            handidiff = dictionary_of_strokes_exchanges[player.name]
            positive_diff = handidiff > 0
            if positive_diff:
                return_statements.append(f"{self.name} receives {handidiff} strokes from {player.name}.")
                handicap_adjust(self_score_lst, handidiff, course_object)
            else:
                return_statements.append(f"{self.name} gives {-handidiff} strokes to {player.name}.")
                handicap_adjust(other_score_lst, abs(handidiff), course_object)
            #Calculate pressures in game
            all_pressures, total_pressures, match = pressures(self_score_lst, other_score_lst)
            #Self bet with player
            pre_lst = pressure_str_func(all_pressures['front9'], all_pressures['back9'])
            self_bet = Bets_Table(player_name=self.name, opponent_name=player.name, course_name=course_name, date=date, strokes_exchanged=handidiff, net_units=units, total_pressures=total_pressures, match=match, hole_string=hole_str, pressures_string1=pre_lst[0], pressures_string2=pre_lst[1], pressures_string3=pre_lst[2], pressures_string4=pre_lst[3], pressures_string5=pre_lst[4])
            self.bets.append(self_bet)
            #Player bet with self - uses conversion == negative of everything
            new_all_ps, new_tot_p, new_match = convert(all_pressures, total_pressures, match)
            oth_pre_lst = pressure_str_func(new_all_ps['front9'], new_all_ps['back9'])
            other_bet = Bets_Table(player_name=player.name, opponent_name=self.name, course_name=course_name, date=date, strokes_exchanged=-handidiff, net_units=-units, total_pressures=new_tot_p, match=new_match, hole_string=hole_str, pressures_string1=oth_pre_lst[0], pressures_string2=oth_pre_lst[1], pressures_string3=oth_pre_lst[2], pressures_string4=oth_pre_lst[3], pressures_string5=oth_pre_lst[4])
            player.bets.append(other_bet)
        return return_statements


class Courses_Table(db.Model):
    __tablename__ = "Courses"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, index=True)
    course_par = db.Column(db.Integer)
    course_par_by_hole = db.relationship("Par_List_Num", back_populates="course_par", lazy='subquery', uselist=False)
    course_handi_by_hole = db.relationship("Handi_List_Num", back_populates="course_handicap", lazy='subquery', uselist=False)

    @staticmethod
    def get_course(i_name):
        return Courses_Table.query.filter_by(name=i_name).first()

    def get_par(self, i=None):
        if isinstance(i, int):
            return self.course_par_by_hole.get(i)
        else:
            return self.course_par_by_hole.get()

    def get_hole_from_diff(self, i=None):
        handi_list = self.course_handi_by_hole.get()
        hole = handi_list.index(i)
        return hole

    @staticmethod
    def create_course(i_name, par_lst, diff_lst):
        par_by_hole = Par_List_Num.create_par_list_num_sql(par_lst)
        diff_by_hole = Handi_List_Num.create_diff_list_num_sql(diff_lst)
        sqlcourse = Courses_Table(name=i_name, course_par=sum(par_lst), course_par_by_hole=par_by_hole, course_handi_by_hole=diff_by_hole)
        return sqlcourse

    def __repr__(self):
        return f"Course {self.name} with par {self.course_par}"

class Scores_Table(db.Model):
    __tablename__ = "Scores"
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey(Players_Table.id), nullable=False)
    player = db.relationship("Players_Table", back_populates="scores")
    player_name = db.Column(db.String(150), nullable=False, index=True)
    course_name = db.Column(db.String(150), nullable=False)
    date = db.Column(db.String(10), index=True)
    total = db.Column(db.Integer)
    score_compared_to_par = db.Column(db.String(3))
    score_by_hole = db.relationship("Score_List_Num", back_populates="score", lazy='select', uselist=False)

    @staticmethod
    def create_score(player_name, score_lst, course_name, par, idate):
        total_strokes = sum(score_lst)
        list_num_object = Score_List_Num.create_score_list_num_sql(score_lst)
        sqlscore = Scores_Table(player_name=player_name, course_name=course_name, date=idate, total=total_strokes, score_compared_to_par=total_strokes-par, score_by_hole=list_num_object)
        return sqlscore


    def get(self, i=None):
        if isinstance(i, int):
            return self.score_by_hole.get(i)
        else:
            return self.score_by_hole.get()

    def __repr__(self):
        return f"Score for player {self.player.name} on {self.date} at {self.course_name}: {self.score} which is {self.score_compared_to_par} to par." + "\n" + self.score_by_hole.__repr__()

class Bets_Table(db.Model):
    __tablename__ = "Bets"
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey(Players_Table.id), nullable=False)
    player = db.relationship("Players_Table", back_populates="bets")
    player_name = db.Column(db.String(150), nullable=False, index=True)
    opponent_name = db.Column(db.String(150), nullable=False)
    course_name = db.Column(db.String(150), nullable=False)
    date = db.Column(db.String(10), index=True)
    strokes_exchanged = db.Column(db.Integer)
    net_units = db.Column(db.Integer)
    total_pressures = db.Column(db.Integer)
    match = db.Column(db.Integer)
    hole_string = db.Column(db.String(40))
    pressures_string1 = db.Column(db.String(40))
    pressures_string2 = db.Column(db.String(40))
    pressures_string3 = db.Column(db.String(40))
    pressures_string4 = db.Column(db.String(40))
    pressures_string5 = db.Column(db.String(40))

    def __repr__(self):
        return f"Bet for player {self.player.name} against {self.opponent_name} on {self.date} at {self.course_name}: strokes exchanged {self.strokes_exchanged}, pressures {self.total_pressures}, and match {self.match}."

    def get_player(self):
        return self.opponent_name

    @staticmethod
    def get_bet(input_id):
        return Bets_Table.query.filter_by(id=input_id).first()

class Score_List_Num(db.Model):
    __tablename__ = "Table for storing Scores"
    id = db.Column(db.Integer, primary_key=True)
    score_id = db.Column(db.Integer, db.ForeignKey(Scores_Table.id), nullable=False)
    score = db.relationship("Scores_Table", back_populates="score_by_hole")
    #player_name = db.Column(db.String(150), db.ForeignKey(Scores_Table.player_name), nullable=False)
    hole_1 = db.Column(db.Integer)
    hole_2 = db.Column(db.Integer)
    hole_3 = db.Column(db.Integer)
    hole_4 = db.Column(db.Integer)
    hole_5 = db.Column(db.Integer)
    hole_6 = db.Column(db.Integer)
    hole_7 = db.Column(db.Integer)
    hole_8 = db.Column(db.Integer)
    hole_9 = db.Column(db.Integer)
    hole_10 = db.Column(db.Integer)
    hole_11 = db.Column(db.Integer)
    hole_12 = db.Column(db.Integer)
    hole_13 = db.Column(db.Integer)
    hole_14 = db.Column(db.Integer)
    hole_15 = db.Column(db.Integer)
    hole_16 = db.Column(db.Integer)
    hole_17 = db.Column(db.Integer)
    hole_18 = db.Column(db.Integer)

    def get(self, i=None):
        lst = self.get_as_list()
        if isinstance(i, int):
            return lst[i]
        else:
            return lst

    def get_as_list(self):
        lst = []
        lst.append(self.hole_1)
        lst.append(self.hole_2)
        lst.append(self.hole_3)
        lst.append(self.hole_4)
        lst.append(self.hole_5)
        lst.append(self.hole_6)
        lst.append(self.hole_7)
        lst.append(self.hole_8)
        lst.append(self.hole_9)
        lst.append(self.hole_10)
        lst.append(self.hole_11)
        lst.append(self.hole_12)
        lst.append(self.hole_13)
        lst.append(self.hole_14)
        lst.append(self.hole_15)
        lst.append(self.hole_16)
        lst.append(self.hole_17)
        lst.append(self.hole_18)
        return lst

    @staticmethod
    def create_score_list_num_sql(lst):
        h1, h2, h3, h4, h5, h6, h7, h8, h9, h10, h11, h12, h13, h14, h15, h16, h17, h18 = lst
        sqllst = Score_List_Num(hole_1=h1, hole_2=h2, hole_3=h3, hole_4=h4, hole_5=h5, hole_6=h6, hole_7=h7, hole_8=h8, hole_9=h9, hole_10=h10, hole_11=h11, hole_12=h12, hole_13=h13, hole_14=h14, hole_15=h15, hole_16=h16, hole_17=h17, hole_18=h18)
        return sqllst

    def __repr__(self):
        front9_str = "  ".join(parse_iter_ent_to_str(range(1,10))) + " | "
        back9_str = " ".join(parse_iter_ent_to_str(range(10,19)))
        hole_str = " Hole: " + front9_str + back9_str
        f9 = f"{self.hole_1}  {self.hole_2}  {self.hole_3}  {self.hole_4}  {self.hole_5}  {self.hole_6}  {self.hole_7}  {self.hole_8}  {self.hole_9}" + " | "
        b9 = f"{self.hole_10}  {self.hole_11}  {self.hole_12}  {self.hole_13}  {self.hole_14}  {self.hole_15}  {self.hole_16}  {self.hole_17}  {self.hole_18}"
        score_str = "Score: " + f9 + b9
        return hole_str + "\n" + score_str

class Par_List_Num(db.Model):
    __tablename__ = "Table for storing course pars"
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey(Courses_Table.id), nullable=False)
    course_par = db.relationship("Courses_Table", back_populates="course_par_by_hole")
    hole_1 = db.Column(db.Integer)
    hole_2 = db.Column(db.Integer)
    hole_3 = db.Column(db.Integer)
    hole_4 = db.Column(db.Integer)
    hole_5 = db.Column(db.Integer)
    hole_6 = db.Column(db.Integer)
    hole_7 = db.Column(db.Integer)
    hole_8 = db.Column(db.Integer)
    hole_9 = db.Column(db.Integer)
    hole_10 = db.Column(db.Integer)
    hole_11 = db.Column(db.Integer)
    hole_12 = db.Column(db.Integer)
    hole_13 = db.Column(db.Integer)
    hole_14 = db.Column(db.Integer)
    hole_15 = db.Column(db.Integer)
    hole_16 = db.Column(db.Integer)
    hole_17 = db.Column(db.Integer)
    hole_18 = db.Column(db.Integer)

    @staticmethod
    def create_par_list_num_sql(lst):
        h1, h2, h3, h4, h5, h6, h7, h8, h9, h10, h11, h12, h13, h14, h15, h16, h17, h18 = lst
        sqllst = Par_List_Num(hole_1=h1, hole_2=h2, hole_3=h3, hole_4=h4, hole_5=h5, hole_6=h6, hole_7=h7, hole_8=h8, hole_9=h9, hole_10=h10, hole_11=h11, hole_12=h12, hole_13=h13, hole_14=h14, hole_15=h15, hole_16=h16, hole_17=h17, hole_18=h18)
        return sqllst

    def get(self, i=None):
        lst = self.get_as_list()
        if isinstance(i, int):
            return lst[i]
        else:
            return lst

    def get_as_list(self):
        lst = []
        lst.append(self.hole_1)
        lst.append(self.hole_2)
        lst.append(self.hole_3)
        lst.append(self.hole_4)
        lst.append(self.hole_5)
        lst.append(self.hole_6)
        lst.append(self.hole_7)
        lst.append(self.hole_8)
        lst.append(self.hole_9)
        lst.append(self.hole_10)
        lst.append(self.hole_11)
        lst.append(self.hole_12)
        lst.append(self.hole_13)
        lst.append(self.hole_14)
        lst.append(self.hole_15)
        lst.append(self.hole_16)
        lst.append(self.hole_17)
        lst.append(self.hole_18)
        return lst

    def __repr__(self):
        front9_str = "  ".join(parse_iter_ent_to_str(range(1,10))) + " | "
        back9_str = " ".join(parse_iter_ent_to_str(range(10,19)))
        hole_str = "Hole: " + front9_str + back9_str
        f9 = f"{self.hole_1}  {self.hole_2}  {self.hole_3}  {self.hole_4}  {self.hole_5}  {self.hole_6}  {self.hole_7}  {self.hole_8}  {self.hole_9}" + " | "
        b9 = f"{self.hole_10}  {self.hole_11}  {self.hole_12}  {self.hole_13}  {self.hole_14}  {self.hole_15}  {self.hole_16}  {self.hole_17}  {self.hole_18}"
        score_str = " Par: " + f9 + b9
        return hole_str + "\n" + score_str

class Handi_List_Num(db.Model):
    __tablename__ = "Table for storing course handicaps"
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey(Courses_Table.id), nullable=False)
    course_handicap = db.relationship("Courses_Table", back_populates="course_handi_by_hole")
    hole_1 = db.Column(db.Integer)
    hole_2 = db.Column(db.Integer)
    hole_3 = db.Column(db.Integer)
    hole_4 = db.Column(db.Integer)
    hole_5 = db.Column(db.Integer)
    hole_6 = db.Column(db.Integer)
    hole_7 = db.Column(db.Integer)
    hole_8 = db.Column(db.Integer)
    hole_9 = db.Column(db.Integer)
    hole_10 = db.Column(db.Integer)
    hole_11 = db.Column(db.Integer)
    hole_12 = db.Column(db.Integer)
    hole_13 = db.Column(db.Integer)
    hole_14 = db.Column(db.Integer)
    hole_15 = db.Column(db.Integer)
    hole_16 = db.Column(db.Integer)
    hole_17 = db.Column(db.Integer)
    hole_18 = db.Column(db.Integer)

    @staticmethod
    def create_diff_list_num_sql(lst):
        h1, h2, h3, h4, h5, h6, h7, h8, h9, h10, h11, h12, h13, h14, h15, h16, h17, h18 = lst
        sqllst = Handi_List_Num(hole_1=h1, hole_2=h2, hole_3=h3, hole_4=h4, hole_5=h5, hole_6=h6, hole_7=h7, hole_8=h8, hole_9=h9, hole_10=h10, hole_11=h11, hole_12=h12, hole_13=h13, hole_14=h14, hole_15=h15, hole_16=h16, hole_17=h17, hole_18=h18)
        return sqllst

    def get(self, i=None):
        lst = self.get_as_list()
        if isinstance(i, int):
            return lst[i]
        else:
            return lst

    def get_as_list(self):
        lst = []
        lst.append(self.hole_1)
        lst.append(self.hole_2)
        lst.append(self.hole_3)
        lst.append(self.hole_4)
        lst.append(self.hole_5)
        lst.append(self.hole_6)
        lst.append(self.hole_7)
        lst.append(self.hole_8)
        lst.append(self.hole_9)
        lst.append(self.hole_10)
        lst.append(self.hole_11)
        lst.append(self.hole_12)
        lst.append(self.hole_13)
        lst.append(self.hole_14)
        lst.append(self.hole_15)
        lst.append(self.hole_16)
        lst.append(self.hole_17)
        lst.append(self.hole_18)
        return lst

    def __repr__(self):
        front9_str = "  ".join(parse_iter_ent_to_str(range(1,10))) + " | "
        back9_str = " ".join(parse_iter_ent_to_str(range(10,19)))
        hole_str = " Hole: " + front9_str + back9_str
        f9 = f"{self.hole_1}  {self.hole_2}  {self.hole_3}  {self.hole_4}  {self.hole_5}  {self.hole_6}  {self.hole_7}  {self.hole_8}  {self.hole_9}" + " | "
        b9 = f"{self.hole_10}  {self.hole_11}  {self.hole_12}  {self.hole_13}  {self.hole_14}  {self.hole_15}  {self.hole_16}  {self.hole_17}  {self.hole_18}"
        score_str = "Handi: " + f9 + b9
        return hole_str + "\n" + score_str




"""db.create_all()
mali = Courses_Table.create_course("Malinalco", [4, 5, 5, 3, 4, 4, 4, 3, 4, 4, 3, 4, 4, 4, 5, 4, 3, 5], [3, 9, 5, 17, 1, 11, 13, 15, 7, 16, 10, 8, 6, 14, 4, 2, 18, 12])
db.session.add(mali)
db.session.commit()"""


#Space
