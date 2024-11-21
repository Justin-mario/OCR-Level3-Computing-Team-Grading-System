from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models.entities import Team, Student, TeamPoints
from app import db
from datetime import datetime
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from sqlalchemy import and_
from app import db
from app.models.entities import Team, Student, TeamLeadership, TeamPoints

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/dashboard')
@login_required
def dashboard():
    teams = Team.query.all()
    # Calculate total points for each team
    for team in teams:
        points = TeamPoints.query.filter_by(team_id=team.id).all()
        team.total_points = sum(p.total_points for p in points)
    return render_template('admin/dashboard.html', teams=teams)


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
            team_id = request.form.get('team_id')
            lesson_date = datetime.strptime(request.form.get('lesson_date'), '%Y-%m-%d').date()
            lesson_number = int(request.form.get('lesson_number'))

            # Check if points already exist for this team, date, and lesson
            existing_points = TeamPoints.query.filter_by(
                team_id=team_id,
                lesson_date=lesson_date,
                lesson_number=lesson_number
            ).first()

            if existing_points:
                flash('Points already recorded for this team, date, and lesson.', 'error')
                return redirect(url_for('admin.add_points', team_id=team_id))

            points = TeamPoints(
                team_id=team_id,
                lesson_date=lesson_date,
                lesson_number=lesson_number,
                attendance_points=float(request.form.get('attendance_points', 0)),
                professional_points=float(request.form.get('professional_points', 0)),
                leadership_points=float(request.form.get('leadership_points', 0)),
                academic_points=float(request.form.get('academic_points', 0)),
                bonus_points=float(request.form.get('bonus_points', 0)),
                phone_penalties=int(request.form.get('phone_penalties', 0))
            )
            points.calculate_total()

            db.session.add(points)
            db.session.commit()

            team = Team.query.get(team_id)
            flash(f'Points recorded successfully for {team.name}', 'success')
            return redirect(url_for('admin.dashboard'))

        except ValueError as e:
            flash(f'Invalid input: {str(e)}', 'error')
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


from datetime import datetime, timedelta


@admin_bp.route('/team/<int:team_id>/leadership', methods=['GET'])
@login_required
def manage_leadership(team_id):
    team = Team.query.get_or_404(team_id)
    today = datetime.now().date()

    # Get current leadership using and_ for explicit conditions
    current_leadership = TeamLeadership.query.filter(and_(
        TeamLeadership.team_id == team_id,
        TeamLeadership.week_start_date <= today,
        TeamLeadership.week_end_date >= today
    )).first()

    # Get leadership history
    leadership_history = TeamLeadership.query.filter_by(team_id=team_id)\
        .order_by(TeamLeadership.week_start_date.desc())\
        .all()

    # Suggest next Monday if no current leader, or next week if there is
    if current_leadership:
        suggested_start = current_leadership.week_end_date + timedelta(days=1)
    else:
        today = datetime.now().date()
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

        # Check if dates overlap with existing leadership using and_
        existing_leadership = TeamLeadership.query.filter(and_(
            TeamLeadership.team_id == team_id,
            TeamLeadership.week_start_date <= week_end,
            TeamLeadership.week_end_date >= week_start
        )).first()

        if existing_leadership:
            flash('There is already a leader assigned for some or all of these dates.', 'error')
            return redirect(url_for('admin.manage_leadership', team_id=team_id))

        # Create new leadership record
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


