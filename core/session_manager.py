#!/usr/bin/env python3
"""Session management for persisting cookies and browser state."""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta


class SessionManager:
    """
    Persist and restore browser sessions (cookies, local storage).

    Sessions are stored in .cache/sessions/{site}_{zipcode}.json
    Each session includes:
    - Cookies
    - Timestamp
    - Zipcode information
    - Expiration time
    """

    def __init__(self, cache_dir: Path = None, max_age_hours: int = 24):
        """
        Initialize session manager.

        Args:
            cache_dir: Directory to store session files (default: .cache/sessions)
            max_age_hours: Maximum age of sessions before they expire (default: 24)
        """
        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent / '.cache' / 'sessions'

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_age = timedelta(hours=max_age_hours)

    def _get_session_path(self, site: str, zipcode: str) -> Path:
        """
        Get file path for session storage.

        Args:
            site: Site name (e.g., 'walmart')
            zipcode: Zipcode

        Returns:
            Path to session file
        """
        filename = f"{site}_{zipcode}.json"
        return self.cache_dir / filename

    def save_session(
        self,
        site: str,
        zipcode: str,
        cookies: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Save session to disk.

        Args:
            site: Site name
            zipcode: Zipcode
            cookies: List of cookie dictionaries from browser
            metadata: Optional additional metadata to store
        """
        session_data = {
            'site': site,
            'zipcode': zipcode,
            'cookies': cookies,
            'metadata': metadata or {},
            'created_at': datetime.now().isoformat(),
            'version': '1.0',
        }

        session_path = self._get_session_path(site, zipcode)

        try:
            with open(session_path, 'w') as f:
                json.dump(session_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save session for {site}/{zipcode}: {e}")

    def load_session(self, site: str, zipcode: str) -> Optional[Dict[str, Any]]:
        """
        Load session from disk.

        Args:
            site: Site name
            zipcode: Zipcode

        Returns:
            Session data dictionary if valid session exists, None otherwise
        """
        session_path = self._get_session_path(site, zipcode)

        if not session_path.exists():
            return None

        try:
            with open(session_path, 'r') as f:
                session_data = json.load(f)

            # Validate session
            if not self.is_session_valid(session_data):
                # Delete expired session
                session_path.unlink()
                return None

            return session_data

        except Exception as e:
            print(f"Warning: Failed to load session for {site}/{zipcode}: {e}")
            return None

    def is_session_valid(self, session: Dict[str, Any]) -> bool:
        """
        Check if session is still valid (not expired).

        Args:
            session: Session data dictionary

        Returns:
            True if session is valid, False if expired
        """
        if not session or 'created_at' not in session:
            return False

        try:
            created_at = datetime.fromisoformat(session['created_at'])
            age = datetime.now() - created_at
            return age < self.max_age
        except Exception:
            return False

    def delete_session(self, site: str, zipcode: str) -> bool:
        """
        Delete a session file.

        Args:
            site: Site name
            zipcode: Zipcode

        Returns:
            True if session was deleted, False if it didn't exist
        """
        session_path = self._get_session_path(site, zipcode)

        if session_path.exists():
            session_path.unlink()
            return True

        return False

    def get_cookies(self, site: str, zipcode: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get cookies from a saved session.

        Args:
            site: Site name
            zipcode: Zipcode

        Returns:
            List of cookie dictionaries, or None if no valid session exists
        """
        session = self.load_session(site, zipcode)
        if session:
            return session.get('cookies', [])
        return None

    def list_sessions(self, site: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all stored sessions, optionally filtered by site.

        Args:
            site: Optional site name to filter by

        Returns:
            List of session metadata dictionaries
        """
        sessions = []

        for session_file in self.cache_dir.glob('*.json'):
            try:
                with open(session_file, 'r') as f:
                    session_data = json.load(f)

                # Filter by site if specified
                if site and session_data.get('site') != site:
                    continue

                sessions.append({
                    'site': session_data.get('site'),
                    'zipcode': session_data.get('zipcode'),
                    'created_at': session_data.get('created_at'),
                    'valid': self.is_session_valid(session_data),
                })
            except Exception:
                continue

        return sessions

    def cleanup_expired(self) -> int:
        """
        Delete all expired sessions.

        Returns:
            Number of sessions deleted
        """
        deleted_count = 0

        for session_file in self.cache_dir.glob('*.json'):
            try:
                with open(session_file, 'r') as f:
                    session_data = json.load(f)

                if not self.is_session_valid(session_data):
                    session_file.unlink()
                    deleted_count += 1
            except Exception:
                continue

        return deleted_count

    def clear_all(self, site: Optional[str] = None) -> int:
        """
        Clear all sessions, optionally filtered by site.

        Args:
            site: Optional site name to filter by

        Returns:
            Number of sessions deleted
        """
        deleted_count = 0

        pattern = f"{site}_*.json" if site else "*.json"

        for session_file in self.cache_dir.glob(pattern):
            try:
                session_file.unlink()
                deleted_count += 1
            except Exception:
                continue

        return deleted_count

    def __str__(self) -> str:
        """String representation."""
        session_count = len(list(self.cache_dir.glob('*.json')))
        return (
            f"SessionManager(cache_dir='{self.cache_dir}', "
            f"sessions={session_count}, max_age={self.max_age.total_seconds()/3600}h)"
        )
