from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    avatar_url = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    members = db.relationship('Student', backref='team', lazy=True)
    points = db.relationship('TeamPoints', backref='team', lazy=True)
    leadership_schedule = db.relationship('TeamLeadership', backref='team', lazy=True)

    # def get_current_leader(self):
    #     """Get the current team leader based on the current week"""
    #     current_date = datetime.utcnow().date()
    #     leadership = TeamLeadership.query.filter(
    #         TeamLeadership.team_id == self.id,
    #         TeamLeadership.week_start_date <= current_date,
    #         TeamLeadership.week_end_date >= current_date
    #     ).first()
    #
    #     if leadership and leadership.leader:
    #         return leadership.leader.first_name
    #     return None
    #
    # def get_metrics(self):
    #     total_points = 0
    #     attendance = 0
    #     professional = 0
    #     leadership = 0
    #     academic = 0
    #     count = 0
    #
    #     for point in self.points:
    #         total_points += point.total_points
    #         attendance += point.attendance_points
    #         professional += point.professional_points
    #         leadership += point.leadership_points
    #         academic += point.academic_points
    #         count += 1
    #
    #     if count > 0:
    #         return {
    #             'total': total_points,
    #             'attendance': round(attendance / count, 1),
    #             'professional': round(professional / count, 1),
    #             'leadership': round(leadership / count, 1),
    #             'academic': round(academic / count, 1)
    #         }
    #     return {
    #         'total': 0,
    #         'attendance': 0,
    #         'professional': 0,
    #         'leadership': 0,
    #         'academic': 0
    #     }
    def get_metrics(self):
        from sqlalchemy import func
        from app import db

        # Get sums instead of averages
        metrics = db.session.query(
            func.sum(TeamPoints.attendance_points).label('attendance'),
            func.sum(TeamPoints.professional_points).label('professional'),
            func.sum(TeamPoints.leadership_points).label('leadership'),
            func.sum(TeamPoints.academic_points).label('academic'),
            func.sum(TeamPoints.total_points).label('total')
        ).filter(TeamPoints.team_id == self.id).first()

        return {
            'total': round(metrics.total or 0, 1),
            'attendance': round(metrics.attendance or 0, 1),
            'professional': round(metrics.professional or 0, 1),
            'leadership': round(metrics.leadership or 0, 1),
            'academic': round(metrics.academic or 0, 1)
        }

    def get_current_leader(self):
        from datetime import datetime
        current_date = datetime.utcnow().date()

        leadership = TeamLeadership.query.join(Student).filter(
            TeamLeadership.team_id == self.id,
            TeamLeadership.week_start_date <= current_date,
            TeamLeadership.week_end_date >= current_date
        ).first()

        if leadership and leadership.leader:
            return leadership.leader.first_name
        return "Not set"


    def calculate_total_points(self):
        return sum(p.total_points for p in self.points)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)


class TeamLeadership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    leader_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    week_start_date = db.Column(db.Date, nullable=False)
    week_end_date = db.Column(db.Date, nullable=False)

    # Add this relationship
    leader = db.relationship('Student', backref='leadership_assignments', lazy=True)


class TeamPoints(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    lesson_date = db.Column(db.Date, nullable=False)
    lesson_number = db.Column(db.Integer, nullable=False)
    attendance_points = db.Column(db.Float, default=0)
    professional_points = db.Column(db.Float, default=0)
    leadership_points = db.Column(db.Float, default=0)
    academic_points = db.Column(db.Float, default=0)
    bonus_points = db.Column(db.Float, default=0)
    phone_penalties = db.Column(db.Integer, default=0)
    total_points = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def calculate_total(self):
        self.total_points = (
                self.attendance_points +
                self.professional_points +
                self.leadership_points +
                self.academic_points +
                self.bonus_points -
                (self.phone_penalties * 3)
        )