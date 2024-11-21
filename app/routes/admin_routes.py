from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from sqlalchemy import func, and_
from app import db
from app.models.entities import Team, Student, TeamLeadership, TeamPoints
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/dashboard')
@login_required
def dashboard():
    teams = Team.query.all()
    end_date = datetime.now().date()
    start_date = end_date - timedelta(weeks=4)

    # Print debug info
    print("\n=== Debug Info ===")
    print(f"Number of teams: {len(teams)}")
    print(f"Date range: {start_date} to {end_date}")

    # Calculate weekly performance data
    weekly_data = {
        'labels': [],
        'datasets': []
    }

    # Generate week labels
    current_date = start_date
    while current_date <= end_date:
        week_start = current_date - timedelta(days=current_date.weekday())
        week_end = week_start + timedelta(days=6)
        weekly_data['labels'].append(week_start.strftime('%Y-%m-%d'))
        current_date += timedelta(days=7)

    for team in teams:
        weekly_totals = []
        current_date = start_date

        while current_date <= end_date:
            week_start = current_date - timedelta(days=current_date.weekday())
            week_end = week_start + timedelta(days=6)

            # Get points for this week
            week_points = db.session.query(
                func.sum(TeamPoints.total_points).label('total')
            ).filter(
                TeamPoints.team_id == team.id,
                TeamPoints.lesson_date >= week_start,
                TeamPoints.lesson_date <= week_end
            ).scalar() or 0

            weekly_totals.append(float(week_points))
            current_date += timedelta(days=7)

        dataset = {
            'label': team.name,
            'data': weekly_totals,
            'fill': False,
            'tension': 0.1
        }
        weekly_data['datasets'].append(dataset)

    # Print weekly data
    print("\nWeekly Data:")
    print(weekly_data)

    # Calculate team comparison data
    teams_data = []
    for team in teams:
        points = TeamPoints.query.filter_by(team_id=team.id).all()
        if points:
            attendance_avg = sum(p.attendance_points for p in points) / len(points)
            professional_avg = sum(p.professional_points for p in points) / len(points)
            leadership_avg = sum(p.leadership_points for p in points) / len(points)
            academic_avg = sum(p.academic_points for p in points) / len(points)
        else:
            attendance_avg = professional_avg = leadership_avg = academic_avg = 0

        teams_data.append({
            'label': team.name,
            'data': [
                float(attendance_avg),
                float(professional_avg),
                float(leadership_avg),
                float(academic_avg)
            ]
        })

    # Print teams data
    print("\nTeams Data:")
    print(teams_data)

    # Calculate penalties data
    penalties_data = {
        'labels': [team.name for team in teams],
        'datasets': [{
            'label': 'Phone Penalties',
            'data': [
                sum(point.phone_penalties for point in team.points)
                for team in teams
            ]
        }]
    }

    # Print penalties data
    print("\nPenalties Data:")
    print(penalties_data)

    # Calculate ranking history
    ranking_history = []
    current_date = start_date
    while current_date <= end_date:
        rankings = []
        for team in teams:
            total_points = sum(
                point.total_points
                for point in team.points
                if point.lesson_date <= current_date
            )
            rankings.append((team.id, total_points))

        rankings.sort(key=lambda x: x[1], reverse=True)
        ranking_dict = {team_id: rank + 1 for rank, (team_id, _) in enumerate(rankings)}
        ranking_history.append((current_date, ranking_dict))
        current_date += timedelta(days=7)

    ranking_data = {
        'labels': [date.strftime('%Y-%m-%d') for date, _ in ranking_history],
        'datasets': [{
            'label': team.name,
            'data': [ranks[team.id] for _, ranks in ranking_history]
        } for team in teams]
    }

    # Print ranking data
    print("\nRanking Data:")
    print(ranking_data)

    # Calculate total points
    for team in teams:
        team.total_points = sum(point.total_points for point in team.points)
        print(f"\nTeam {team.name} total points: {team.total_points}")

    return render_template('admin/dashboard.html',
                         teams=teams,
                         weekly_data=weekly_data,
                         teams_data=teams_data,
                         penalties_data=penalties_data,
                         ranking_data=ranking_data,
                         teams_count=len(teams))
@admin_bp.route('/team/add', methods=['GET', 'POST'])
@login_required
def add_team():
    if request.method == 'POST':
        name = request.form.get('name')
        avatar_url = request.form.get('avatar_url')

        if not name:
            flash('Team name is required', 'error')
            return redirect(url_for('admin.add_team'))

        team = Team(name=name, avatar_url=avatar_url)
        db.session.add(team)
        try:
            db.session.commit()
            flash('Team created successfully', 'success')
            return redirect(url_for('admin.dashboard'))
        except:
            db.session.rollback()
            flash('Error creating team. Name might be taken.', 'error')

    return render_template('admin/teams.html')

@admin_bp.route('/points/add', methods=['GET', 'POST'])
@login_required
def add_points():
    teams = Team.query.all()
    selected_team_id = request.args.get('team_id')
    today_date = datetime.now().strftime('%Y-%m-%d')

    if request.method == 'POST':
        try:
            # Validate points
            attendance_points = float(request.form.get('attendance_points', 0))
            professional_points = float(request.form.get('professional_points', 0))
            leadership_points = float(request.form.get('leadership_points', 0))
            academic_points = float(request.form.get('academic_points', 0))
            bonus_points = float(request.form.get('bonus_points', 0))
            phone_penalties = int(request.form.get('phone_penalties', 0))

            # Validate ranges
            if not (0 <= attendance_points <= 10):
                raise ValueError("Attendance points must be between 0 and 10")
            if not (0 <= professional_points <= 10):
                raise ValueError("Professional points must be between 0 and 10")
            if not (0 <= leadership_points <= 10):
                raise ValueError("Leadership points must be between 0 and 10")
            if not (0 <= academic_points <= 20):
                raise ValueError("Academic points must be between 0 and 20")
            if not (0 <= bonus_points <= 5):
                raise ValueError("Bonus points must be between 0 and 5")

            # Check for existing points
            team_id = request.form.get('team_id')
            lesson_date = datetime.strptime(request.form.get('lesson_date'), '%Y-%m-%d').date()
            lesson_number = int(request.form.get('lesson_number'))

            existing_points = TeamPoints.query.filter_by(
                team_id=team_id,
                lesson_date=lesson_date,
                lesson_number=lesson_number
            ).first()

            if existing_points:
                flash('Points already recorded for this team, date, and lesson.', 'error')
                return redirect(url_for('admin.add_points', team_id=team_id))

            # Create and save points
            points = TeamPoints(
                team_id=team_id,
                lesson_date=lesson_date,
                lesson_number=lesson_number,
                attendance_points=attendance_points,
                professional_points=professional_points,
                leadership_points=leadership_points,
                academic_points=academic_points,
                bonus_points=bonus_points,
                phone_penalties=phone_penalties
            )
            points.calculate_total()

            db.session.add(points)
            db.session.commit()
            flash('Points recorded successfully!', 'success')
            return redirect(url_for('admin.dashboard'))

        except ValueError as e:
            flash(str(e), 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error recording points: {str(e)}', 'error')

    return render_template('admin/points.html',
                         teams=teams,
                         selected_team_id=selected_team_id,
                         today_date=today_date)

@admin_bp.route('/team/<int:team_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_team(team_id):
    team = Team.query.get_or_404(team_id)

    if request.method == 'POST':
        team.name = request.form.get('name', team.name)
        team.avatar_url = request.form.get('avatar_url', team.avatar_url)

        try:
            db.session.commit()
            flash('Team updated successfully', 'success')
            return redirect(url_for('admin.dashboard'))
        except:
            db.session.rollback()
            flash('Error updating team', 'error')

    return render_template('admin/teams.html', team=team)

@admin_bp.route('/team/<int:team_id>/members', methods=['GET', 'POST'])
@login_required
def manage_members(team_id):
    team = Team.query.get_or_404(team_id)

    if request.method == 'POST':
        first_name = request.form.get('first_name')
        if first_name:
            student = Student(first_name=first_name, team_id=team.id)
            db.session.add(student)
            try:
                db.session.commit()
                flash('Member added successfully', 'success')
            except:
                db.session.rollback()
                flash('Error adding member', 'error')

    return render_template('admin/members.html', team=team)

@admin_bp.route('/team/<int:team_id>/member/<int:member_id>/remove', methods=['POST'])
@login_required
def remove_member(team_id, member_id):
    team = Team.query.get_or_404(team_id)
    member = Student.query.get_or_404(member_id)

    if member.team_id != team.id:
        flash('Invalid request', 'error')
        return redirect(url_for('admin.manage_members', team_id=team.id))

    try:
        db.session.delete(member)
        db.session.commit()
        flash(f'Successfully removed {member.first_name} from the team', 'success')
    except:
        db.session.rollback()
        flash('Error removing team member', 'error')

    return redirect(url_for('admin.manage_members', team_id=team.id))

@admin_bp.route('/team/<int:team_id>/leadership', methods=['GET'])
@login_required
def manage_leadership(team_id):
    team = Team.query.get_or_404(team_id)
    today = datetime.now().date()

    current_leadership = TeamLeadership.query.filter(and_(
        TeamLeadership.team_id == team_id,
        TeamLeadership.week_start_date <= today,
        TeamLeadership.week_end_date >= today
    )).first()

    leadership_history = TeamLeadership.query.filter_by(team_id=team_id)\
        .order_by(TeamLeadership.week_start_date.desc())\
        .all()

    if current_leadership:
        suggested_start = current_leadership.week_end_date + timedelta(days=1)
    else:
        days_until_monday = (7 - today.weekday()) % 7
        suggested_start = today + timedelta(days=days_until_monday)

    return render_template('admin/leadership.html',
                         team=team,
                         current_leadership=current_leadership,
                         leadership_history=leadership_history,
                         suggested_start_date=suggested_start.strftime('%Y-%m-%d'))

@admin_bp.route('/team/<int:team_id>/leadership/assign', methods=['POST'])
@login_required
def assign_leader(team_id):
    team = Team.query.get_or_404(team_id)

    try:
        leader_id = request.form.get('leader_id')
        week_start = datetime.strptime(request.form.get('week_start_date'), '%Y-%m-%d').date()
        week_end = week_start + timedelta(days=6)

        existing_leadership = TeamLeadership.query.filter(and_(
            TeamLeadership.team_id == team_id,
            TeamLeadership.week_start_date <= week_end,
            TeamLeadership.week_end_date >= week_start
        )).first()

        if existing_leadership:
            flash('There is already a leader assigned for some or all of these dates.', 'error')
            return redirect(url_for('admin.manage_leadership', team_id=team_id))

        leadership = TeamLeadership(
            team_id=team_id,
            leader_id=leader_id,
            week_start_date=week_start,
            week_end_date=week_end
        )

        db.session.add(leadership)
        db.session.commit()
        flash('Team leader assigned successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error assigning team leader: {str(e)}', 'error')

    return redirect(url_for('admin.manage_leadership', team_id=team_id))