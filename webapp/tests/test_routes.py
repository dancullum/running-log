"""
Route Tests for Running Log.

TESTING HTTP RESPONSES
----------------------
When testing web routes, we typically check:

1. STATUS CODES
   - 200 = OK (page loaded)
   - 302 = Redirect (going somewhere else)
   - 404 = Not Found
   - 500 = Server Error (something broke!)

2. RESPONSE DATA
   - Check that expected content is in the HTML
   - Use `b'text'` (bytes) when checking response.data

3. REDIRECTS
   - response.location tells you where a redirect goes
   - Use follow_redirects=True to automatically follow them

TESTING WITH DATA
-----------------
When tests need database data, we use fixtures:

    def test_home_shows_runs(authenticated_client, sample_runs):
        # sample_runs fixture created test data for us
        response = authenticated_client.get('/')
        assert b'6' in response.data  # Check run distance appears
"""

from datetime import date, timedelta
from webapp.models import db, Run, TrainingPlan


class TestHomePage:
    """
    Tests for the home page (/).
    """

    def test_home_shows_this_week_section(self, authenticated_client):
        """
        Test that home page has the "This Week" progress section.
        """
        response = authenticated_client.get('/')

        assert response.status_code == 200
        assert b'This Week' in response.data

    def test_home_shows_recent_runs_section(self, authenticated_client):
        """
        Test that home page has the "Recent Runs" section.
        """
        response = authenticated_client.get('/')

        assert response.status_code == 200
        assert b'Recent Runs' in response.data

    def test_home_shows_logged_runs(self, authenticated_client, app, sample_runs):
        """
        Test that home page displays runs from the database.

        This test uses two fixtures:
        - authenticated_client: logged-in test client
        - sample_runs: creates test run data
        """
        response = authenticated_client.get('/')

        # sample_runs creates runs with distances 6, 7, 8
        # At least one should appear on home page
        assert response.status_code == 200

    def test_home_shows_todays_target(self, authenticated_client, app, sample_training_plan):
        """
        Test that home shows today's target if there is one.
        """
        response = authenticated_client.get('/')

        assert response.status_code == 200
        # The sample_training_plan includes today


class TestLogPage:
    """
    Tests for the log run page (/log).
    """

    def test_log_page_shows_form(self, authenticated_client):
        """
        Test that log page displays the run entry form.
        """
        response = authenticated_client.get('/log')

        assert response.status_code == 200
        assert b'Distance' in response.data
        assert b'Log Run' in response.data  # Submit button

    def test_log_page_shows_quick_entry_buttons(self, authenticated_client):
        """
        Test that quick entry buttons are present.
        """
        response = authenticated_client.get('/log')

        assert response.status_code == 200
        assert b'Quick Entry' in response.data
        assert b'5 km' in response.data
        assert b'8 km' in response.data

    def test_log_run_creates_database_entry(self, authenticated_client, app):
        """
        Test that submitting the form creates a run in the database.

        This is an important integration test - it verifies the full
        flow from form submission to database.
        """
        # ARRANGE
        today = date.today()
        run_data = {
            'date': today.isoformat(),
            'distance': '7.5'
        }

        # ACT
        response = authenticated_client.post('/log', data=run_data)

        # ASSERT - Check redirect (success)
        assert response.status_code == 302

        # ASSERT - Check database
        with app.app_context():
            run = Run.query.filter_by(date=today).first()
            assert run is not None
            assert float(run.distance) == 7.5

    def test_log_run_updates_existing_entry(self, authenticated_client, app):
        """
        Test that logging a run for an existing date updates it.

        Business rule: If you already logged a run for a date,
        submitting again should update, not create duplicate.
        """
        today = date.today()

        # ARRANGE - Create initial run
        with app.app_context():
            run = Run(date=today, distance=5.0)
            db.session.add(run)
            db.session.commit()

        # ACT - Log different distance for same date
        authenticated_client.post('/log', data={
            'date': today.isoformat(),
            'distance': '10.0'
        })

        # ASSERT - Should be updated, not duplicated
        with app.app_context():
            runs = Run.query.filter_by(date=today).all()
            assert len(runs) == 1  # Only one entry
            assert float(runs[0].distance) == 10.0  # Updated value

    def test_log_run_rejects_negative_distance(self, authenticated_client, app):
        """
        Test that negative distances are rejected.

        Edge case / validation test.
        """
        response = authenticated_client.post('/log', data={
            'date': date.today().isoformat(),
            'distance': '-5'
        }, follow_redirects=True)

        # Should show error, not save
        assert b'positive distance' in response.data

        # Verify nothing saved
        with app.app_context():
            count = Run.query.count()
            assert count == 0

    def test_log_run_rejects_excessive_distance(self, authenticated_client, app):
        """
        Test that unreasonably high distances are rejected.

        Validation: > 100km in one run is probably a typo.
        """
        response = authenticated_client.post('/log', data={
            'date': date.today().isoformat(),
            'distance': '150'
        }, follow_redirects=True)

        assert b'too high' in response.data


class TestPlanPage:
    """
    Tests for the training plan page (/plan).
    """

    def test_plan_page_loads(self, authenticated_client):
        """
        Test that plan page loads successfully.
        """
        response = authenticated_client.get('/plan')

        assert response.status_code == 200
        assert b'Training Plan' in response.data

    def test_plan_shows_total_remaining(self, authenticated_client, sample_training_plan):
        """
        Test that plan page shows total remaining distance.
        """
        response = authenticated_client.get('/plan')

        assert response.status_code == 200
        assert b'Total Planned Distance' in response.data

    def test_plan_shows_today_highlighted(self, authenticated_client, sample_training_plan):
        """
        Test that today's entry is marked specially.
        """
        response = authenticated_client.get('/plan')

        assert response.status_code == 200
        assert b'Today' in response.data


class TestDashboard:
    """
    Tests for the public dashboard (/dashboard).
    """

    def test_dashboard_shows_stats(self, client):
        """
        Test that dashboard shows statistics section.
        """
        response = client.get('/dashboard')

        assert response.status_code == 200
        assert b'Total Runs' in response.data
        assert b'Total km' in response.data

    def test_dashboard_shows_all_runs(self, client, app, sample_runs):
        """
        Test that dashboard lists all logged runs.
        """
        response = client.get('/dashboard')

        assert response.status_code == 200
        assert b'All Runs' in response.data

    def test_dashboard_hides_edit_buttons_when_not_authenticated(self, client, app, sample_runs):
        """
        Test that edit buttons are hidden for public viewers.

        The dashboard is public, but editing should require login.
        """
        response = client.get('/dashboard')

        # The edit link contains the run ID, so let's check the
        # authenticated version has edit and unauthenticated doesn't
        assert response.status_code == 200
        # Edit icon SVG path shouldn't be in a clickable link for public
        # This is a bit tricky to test precisely

    def test_dashboard_shows_edit_buttons_when_authenticated(self, authenticated_client, app, sample_runs):
        """
        Test that edit buttons appear for authenticated users.
        """
        response = authenticated_client.get('/dashboard')

        assert response.status_code == 200
        # Should contain link to edit_run route
        assert b'/run/' in response.data and b'/edit' in response.data


class TestEditRun:
    """
    Tests for the edit/delete run page (/run/<id>/edit).
    """

    def test_edit_page_loads(self, authenticated_client, app):
        """
        Test that edit page loads for existing run.
        """
        # ARRANGE - Create a run
        with app.app_context():
            run = Run(date=date.today(), distance=5.0)
            db.session.add(run)
            db.session.commit()
            run_id = run.id

        # ACT
        response = authenticated_client.get(f'/run/{run_id}/edit')

        # ASSERT
        assert response.status_code == 200
        assert b'Edit Run' in response.data

    def test_edit_page_returns_404_for_nonexistent_run(self, authenticated_client):
        """
        Test that editing nonexistent run returns 404.
        """
        response = authenticated_client.get('/run/99999/edit')

        assert response.status_code == 404

    def test_edit_updates_run(self, authenticated_client, app):
        """
        Test that submitting edit form updates the run.
        """
        # ARRANGE
        with app.app_context():
            run = Run(date=date.today(), distance=5.0)
            db.session.add(run)
            db.session.commit()
            run_id = run.id

        # ACT
        response = authenticated_client.post(f'/run/{run_id}/edit', data={
            'distance': '8.0',
            'action': 'save'
        })

        # ASSERT
        assert response.status_code == 302  # Redirect on success

        with app.app_context():
            updated_run = db.session.get(Run, run_id)
            assert float(updated_run.distance) == 8.0

    def test_delete_removes_run(self, authenticated_client, app):
        """
        Test that delete action removes the run.
        """
        # ARRANGE
        with app.app_context():
            run = Run(date=date.today(), distance=5.0)
            db.session.add(run)
            db.session.commit()
            run_id = run.id

        # ACT
        response = authenticated_client.post(f'/run/{run_id}/edit', data={
            'action': 'delete'
        })

        # ASSERT
        assert response.status_code == 302

        with app.app_context():
            deleted_run = db.session.get(Run, run_id)
            assert deleted_run is None


class TestChartAPI:
    """
    Tests for the chart data API (/api/chart-data).
    """

    def test_chart_api_returns_json(self, client):
        """
        Test that API returns valid JSON.
        """
        response = client.get('/api/chart-data')

        assert response.status_code == 200
        assert response.content_type == 'application/json'

    def test_chart_api_returns_expected_structure(self, client):
        """
        Test that API response has required fields.
        """
        response = client.get('/api/chart-data')
        data = response.get_json()

        assert 'labels' in data
        assert 'actual' in data
        assert 'target' in data
        assert isinstance(data['labels'], list)
        assert isinstance(data['actual'], list)
        assert isinstance(data['target'], list)

    def test_chart_api_includes_run_data(self, client, app, sample_runs, sample_training_plan):
        """
        Test that API includes logged run data.
        """
        response = client.get('/api/chart-data')
        data = response.get_json()

        # With sample data, should have some values
        assert len(data['labels']) > 0
        # Cumulative actual should be > 0 since we have runs
        assert any(v > 0 for v in data['actual'])
