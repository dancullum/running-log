"""Tests for Strava integration."""

import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import patch, MagicMock

from webapp.models import db, Run, StravaToken
from webapp.services import strava as strava_service


class TestStravaModels:
    """Test Strava-related model functionality."""

    def test_strava_token_is_expired(self, app):
        """Test token expiration check."""
        with app.app_context():
            # Expired token
            expired_token = StravaToken(
                athlete_id=12345,
                access_token='expired',
                refresh_token='refresh',
                expires_at=int(datetime(2020, 1, 1).timestamp()),
            )
            assert expired_token.is_expired() is True

            # Valid token (far future)
            valid_token = StravaToken(
                athlete_id=12345,
                access_token='valid',
                refresh_token='refresh',
                expires_at=int(datetime(2099, 1, 1).timestamp()),
            )
            assert valid_token.is_expired() is False

    def test_run_pace_formatted(self, app):
        """Test pace formatting."""
        with app.app_context():
            run = Run(
                date=date.today(),
                distance=Decimal('5.00'),
                pace=Decimal('5.50'),  # 5:30/km
            )
            assert run.pace_formatted == '5:30'

            run2 = Run(
                date=date.today(),
                distance=Decimal('5.00'),
                pace=Decimal('4.25'),  # 4:15/km
            )
            assert run2.pace_formatted == '4:15'

            run3 = Run(
                date=date.today(),
                distance=Decimal('5.00'),
                pace=None,
            )
            assert run3.pace_formatted is None

    def test_run_duration_formatted(self, app):
        """Test duration formatting."""
        with app.app_context():
            # Under 1 hour
            run = Run(
                date=date.today(),
                distance=Decimal('5.00'),
                duration=1845,  # 30:45
            )
            assert run.duration_formatted == '30:45'

            # Over 1 hour
            run2 = Run(
                date=date.today(),
                distance=Decimal('10.00'),
                duration=3725,  # 1:02:05
            )
            assert run2.duration_formatted == '1:02:05'

            run3 = Run(
                date=date.today(),
                distance=Decimal('5.00'),
                duration=None,
            )
            assert run3.duration_formatted is None


class TestStravaService:
    """Test Strava service functions."""

    def test_is_strava_connected_false(self, app):
        """Test is_strava_connected when not connected."""
        with app.app_context():
            assert strava_service.is_strava_connected() is False

    def test_is_strava_connected_true(self, app):
        """Test is_strava_connected when connected."""
        with app.app_context():
            token = StravaToken(
                athlete_id=12345,
                access_token='test',
                refresh_token='test',
                expires_at=9999999999,
            )
            db.session.add(token)
            db.session.commit()

            assert strava_service.is_strava_connected() is True

    def test_disconnect_strava(self, app):
        """Test disconnecting Strava."""
        with app.app_context():
            token = StravaToken(
                athlete_id=12345,
                access_token='test',
                refresh_token='test',
                expires_at=9999999999,
            )
            db.session.add(token)
            db.session.commit()

            assert strava_service.is_strava_connected() is True
            strava_service.disconnect_strava()
            assert strava_service.is_strava_connected() is False

    def test_sync_activities_to_db(self, app):
        """Test syncing activities to database."""
        with app.app_context():
            activities = [
                {
                    'id': 123456789,
                    'type': 'Run',
                    'distance': 5000,  # 5km in meters
                    'moving_time': 1500,  # 25 minutes
                    'start_date_local': '2025-01-20T07:00:00Z',
                },
                {
                    'id': 123456790,
                    'type': 'Run',
                    'distance': 10000,  # 10km
                    'moving_time': 3000,  # 50 minutes
                    'start_date_local': '2025-01-21T08:00:00Z',
                },
            ]

            synced, skipped = strava_service.sync_activities_to_db(activities)

            assert synced == 2
            assert skipped == 0

            # Verify runs were created
            runs = Run.query.all()
            assert len(runs) == 2

            run1 = Run.query.filter_by(strava_activity_id=123456789).first()
            assert run1 is not None
            assert float(run1.distance) == 5.0
            assert run1.duration == 1500
            assert run1.source == 'strava'

    def test_sync_activities_skips_duplicates(self, app):
        """Test that duplicate activities are skipped."""
        with app.app_context():
            # Create existing run
            existing = Run(
                date=date(2025, 1, 20),
                distance=Decimal('5.00'),
                strava_activity_id=123456789,
                source='strava',
            )
            db.session.add(existing)
            db.session.commit()

            activities = [
                {
                    'id': 123456789,  # Same ID as existing
                    'type': 'Run',
                    'distance': 5000,
                    'moving_time': 1500,
                    'start_date_local': '2025-01-20T07:00:00Z',
                },
                {
                    'id': 123456790,  # New activity
                    'type': 'Run',
                    'distance': 10000,
                    'moving_time': 3000,
                    'start_date_local': '2025-01-21T08:00:00Z',
                },
            ]

            synced, skipped = strava_service.sync_activities_to_db(activities)

            assert synced == 1
            assert skipped == 1

            # Only 2 runs total (1 existing + 1 new)
            assert Run.query.count() == 2


class TestStravaRoutes:
    """Test Strava route handlers."""

    def test_connect_requires_auth(self, client):
        """Test that connect requires authentication."""
        response = client.get('/strava/connect')
        assert response.status_code == 302
        assert '/login' in response.location

    @patch.object(strava_service, 'is_strava_connected', return_value=False)
    def test_connect_redirects_to_strava(self, mock_connected, authenticated_client, app):
        """Test that connect redirects to Strava OAuth."""
        with app.app_context():
            app.config['STRAVA_CLIENT_ID'] = 'test_client_id'
            with patch('webapp.config.STRAVA_CLIENT_ID', 'test_client_id'), \
                 patch('webapp.config.STRAVA_CLIENT_SECRET', 'test_secret'):
                response = authenticated_client.get('/strava/connect')
                assert response.status_code == 302
                assert 'strava.com/oauth/authorize' in response.location

    def test_disconnect_removes_token(self, authenticated_client, app):
        """Test that disconnect removes the Strava token."""
        with app.app_context():
            # Add a token
            token = StravaToken(
                athlete_id=12345,
                access_token='test',
                refresh_token='test',
                expires_at=9999999999,
            )
            db.session.add(token)
            db.session.commit()

            response = authenticated_client.post('/strava/disconnect')
            assert response.status_code == 302

            # Token should be removed
            assert StravaToken.query.count() == 0

    @patch.object(strava_service, 'sync_from_strava')
    def test_sync_endpoint(self, mock_sync, authenticated_client, app):
        """Test manual sync endpoint."""
        mock_sync.return_value = ((3, 1), None)

        with app.app_context():
            response = authenticated_client.post('/strava/sync')
            assert response.status_code == 302
            mock_sync.assert_called_once()
