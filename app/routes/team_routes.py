from flask import Blueprint, render_template
from app.models.entities import Team, TeamPoints
from sqlalchemy import func

team_bp = Blueprint('team', __name__)


@team_bp.route('/')
def index():
    teams = Team.query.all()
    teams_data = []

    for team in teams:
        # Calculate total points
        total_points = sum(point.total_points for point in team.points) if team.points else 0

        # Calculate metrics
        metrics = {
            'attendance': sum(point.attendance_points for point in team.points) if team.points else 0,
            'professional': sum(point.professional_points for point in team.points) if team.points else 0,
            'leadership': sum(point.leadership_points for point in team.points) if team.points else 0,
            'academic': sum(point.academic_points for point in team.points) if team.points else 0
        }

        teams_data.append({
            'id': team.id,
            'name': team.name,
            'avatar_url': team.avatar_url,
            'total_points': total_points,
            'current_leader': team.get_current_leader(),
            'metrics': metrics
        })

    # Sort teams by total points
    teams_data.sort(key=lambda x: x['total_points'], reverse=True)
    return render_template('index.html', teams=teams_data)