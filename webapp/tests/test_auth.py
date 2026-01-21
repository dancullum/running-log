"""
Authentication Tests for Running Log.

TEST NAMING CONVENTION
----------------------
Test functions should be named: test_<what>_<expected_behavior>

Examples:
- test_login_with_correct_password_succeeds
- test_protected_route_redirects_when_not_authenticated

This makes test output readable:
    PASSED test_auth.py::test_login_with_correct_password_succeeds
    FAILED test_auth.py::test_login_with_wrong_password_shows_error

ANATOMY OF A TEST
-----------------
Every test follows the AAA pattern:

    def test_something(client):
        # ARRANGE - Set up the test conditions
        data = {'password': 'wrong'}

        # ACT - Perform the action being tested
        response = client.post('/login', data=data)

        # ASSERT - Verify the expected outcome
        assert response.status_code == 200
        assert b'Incorrect password' in response.data
"""


class TestLoginPage:
    """
    Tests for the login page and login process.

    Grouping related tests in a class helps organize them and
    allows sharing setup if needed.
    """

    def test_login_page_loads(self, client):
        """
        Test that the login page is accessible.

        This is a basic "smoke test" - just checking the page loads.
        """
        # ACT
        response = client.get('/login')

        # ASSERT
        assert response.status_code == 200
        assert b'Password' in response.data  # Check form is present

    def test_login_with_correct_password_redirects_to_home(self, client):
        """
        Test successful login redirects to home page.

        When a user enters the correct password, they should be
        redirected to the home page (status 302 = redirect).
        """
        # ARRANGE
        correct_password = 'runninglog2026'

        # ACT
        response = client.post('/login', data={'password': correct_password})

        # ASSERT
        assert response.status_code == 302  # Redirect
        assert '/' in response.location  # Redirects to home

    def test_login_with_wrong_password_shows_error(self, client):
        """
        Test that wrong password shows error message.

        The user should stay on the login page (200) and see
        an error message.
        """
        # ARRANGE
        wrong_password = 'wrongpassword'

        # ACT
        response = client.post(
            '/login',
            data={'password': wrong_password},
            follow_redirects=True  # Follow any redirects
        )

        # ASSERT
        assert response.status_code == 200
        assert b'Incorrect password' in response.data

    def test_login_with_empty_password_stays_on_page(self, client):
        """
        Test that empty password doesn't crash the app.

        Edge case: what happens if someone submits an empty form?
        """
        # ACT
        response = client.post('/login', data={'password': ''})

        # ASSERT - Should stay on login page, not crash
        assert response.status_code in [200, 302]


class TestProtectedRoutes:
    """
    Tests that verify protected routes require authentication.

    These tests ensure our @login_required decorator works correctly.
    """

    def test_home_redirects_to_login_when_not_authenticated(self, client):
        """
        Test that / redirects to login for unauthenticated users.
        """
        response = client.get('/')

        assert response.status_code == 302
        assert '/login' in response.location

    def test_plan_redirects_to_login_when_not_authenticated(self, client):
        """
        Test that /plan redirects to login for unauthenticated users.
        """
        response = client.get('/plan')

        assert response.status_code == 302
        assert '/login' in response.location

    def test_log_redirects_to_login_when_not_authenticated(self, client):
        """
        Test that /log redirects to login for unauthenticated users.
        """
        response = client.get('/log')

        assert response.status_code == 302
        assert '/login' in response.location

    def test_home_accessible_when_authenticated(self, authenticated_client):
        """
        Test that authenticated users can access home page.

        Note: We use 'authenticated_client' fixture here instead of 'client'.
        The fixture handles logging in for us.
        """
        response = authenticated_client.get('/')

        assert response.status_code == 200
        assert b'Running Log' in response.data

    def test_plan_accessible_when_authenticated(self, authenticated_client):
        """
        Test that authenticated users can access plan page.
        """
        response = authenticated_client.get('/plan')

        assert response.status_code == 200

    def test_log_accessible_when_authenticated(self, authenticated_client):
        """
        Test that authenticated users can access log page.
        """
        response = authenticated_client.get('/log')

        assert response.status_code == 200


class TestPublicRoutes:
    """
    Tests for routes that should be publicly accessible.
    """

    def test_dashboard_accessible_without_login(self, client):
        """
        Test that dashboard is public - no login required.

        This is important for the "shareable link" feature.
        """
        response = client.get('/dashboard')

        assert response.status_code == 200
        assert b'Dashboard' in response.data

    def test_chart_api_accessible_without_login(self, client):
        """
        Test that chart data API is public.

        The dashboard needs this API to render the chart.
        """
        response = client.get('/api/chart-data')

        assert response.status_code == 200
        # Should return JSON
        assert response.content_type == 'application/json'


class TestLogout:
    """
    Tests for the logout functionality.
    """

    def test_logout_clears_session(self, authenticated_client):
        """
        Test that logout clears authentication.

        After logout, trying to access a protected route
        should redirect to login again.
        """
        # ACT - Logout
        authenticated_client.get('/logout')

        # ASSERT - Now should be redirected from protected routes
        response = authenticated_client.get('/')
        assert response.status_code == 302
        assert '/login' in response.location

    def test_logout_redirects_to_dashboard(self, authenticated_client):
        """
        Test that logout redirects to public dashboard.
        """
        response = authenticated_client.get('/logout', follow_redirects=False)

        assert response.status_code == 302
        assert '/dashboard' in response.location
