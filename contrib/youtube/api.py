"""YouTube API client for fetching video information from multiple channels."""

import logging
import re

from yt_dlp import YoutubeDL

from contrib.base import BaseClient, NetworkError, ValidationError

logger = logging.getLogger(__name__)


class YouTubeBaseClient(BaseClient):
    """
    Base class for YouTube channel clients.

    Provides common functionality for fetching videos from YouTube channels using yt-dlp.
    Subclasses override _clean_title() to handle channel-specific title formats.
    """

    CHANNEL_URL = None  # Override in subclasses - should be the channel URL (e.g., https://www.youtube.com/@channelname)
    CHANNEL_ID = None  # Override in subclasses - for backward compatibility

    def __init__(self):
        """Initialize YouTube base client."""
        if not self.CHANNEL_URL and not self.CHANNEL_ID:
            raise ValidationError(
                "CHANNEL_URL or CHANNEL_ID must be defined in subclass"
            )
        super().__init__()

    def _validate_config(self):
        """Validate that the client is properly configured."""
        if not self.CHANNEL_URL and not self.CHANNEL_ID:
            raise ValidationError("YouTube CHANNEL_URL or CHANNEL_ID is required")

    def _get_channel_url(self):
        """
        Get the channel URL for yt-dlp extraction.

        Returns:
            str: The channel URL to extract videos from
        """
        if self.CHANNEL_URL:
            return self.CHANNEL_URL
        # Fallback: construct URL from channel ID if only ID is provided
        return f"https://www.youtube.com/channel/{self.CHANNEL_ID}"

    def _fetch_videos(self):
        """
        Fetch videos from YouTube channel using yt-dlp.

        Returns:
            list: List of dictionaries with video data

        Raises:
            NetworkError: If the request fails
        """
        try:
            channel_url = self._get_channel_url()
            logger.debug(f"Fetching videos from: {channel_url}")

            ydl_opts = {
                "extract_flat": "in_playlist",
                "quiet": False,
                "no_warnings": False,
                "socket_timeout": 30,
            }

            with YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(channel_url, download=False)

            if not result or "entries" not in result:
                raise NetworkError("No videos found in channel")

            videos = []
            for entry in result["entries"]:
                video = {
                    "title": entry.get("title", ""),
                    "description": entry.get("description", ""),
                    "published": entry.get("upload_date", ""),
                    "video_url": entry.get("url", ""),
                    "video_id": entry.get("id", ""),
                    "thumbnail": entry.get("thumbnail", ""),
                }
                videos.append(video)

            logger.debug(f"Fetched {len(videos)} videos from channel")
            return videos

        except Exception as e:
            raise NetworkError(f"Error fetching YouTube videos: {e}") from e

    def _extract_year(self, title):
        """
        Extract year from title (format: any text with (YYYY)).

        Args:
            title (str): Video title

        Returns:
            int or None: Year if found, None otherwise
        """
        match = re.search(r"\((\d{4})\)", title)
        if match:
            return int(match.group(1))
        return None

    def _extract_title_and_id(self, videos):
        """
        Extract title, year, and video_id from parsed videos.

        Args:
            videos (list): List of video dicts with title, video_id, etc.

        Returns:
            list: List of dicts with cleaned title, year, original_title, and video_id
        """
        processed = []
        for video in videos:
            original_title = video["title"]

            # Clean title using channel-specific logic
            cleaned_title = self._clean_title(original_title)

            # Skip if title doesn't match channel format
            if cleaned_title is None:
                continue

            # Extract year
            year = self._extract_year(original_title)

            # Video ID is already extracted by yt-dlp
            video_id = video.get("video_id", "")

            processed.append(
                {
                    "title": cleaned_title,
                    "year": year,
                    "original_title": original_title,
                    "video_id": video_id,
                }
            )
        return processed

    def get_data(self, **kwargs):
        """
        Main method to fetch and parse YouTube videos.

        Returns:
            list: List of video dictionaries with title and video_id

        Raises:
            NetworkError: If fetching fails
            ValidationError: If parsing fails
        """
        videos = self._fetch_videos()
        processed_videos = self._extract_title_and_id(videos)
        return processed_videos


class MubiClient(YouTubeBaseClient):
    """
    Mubi channel client.

    Handles Mubi-specific title format.
    Override _clean_title() with Mubi-specific parsing logic.
    """

    CHANNEL_URL = "https://www.youtube.com/@mubi/videos"
    CHANNEL_ID = "UCb6-VM5UQ4Czj_d3m9EPGfg"  # Fallback for backward compatibility

    def _clean_title(self, title):
        """
        Extract movie title from Mubi title format.

        Format: "MOVIE TITLE | Official Trailer #1 | ..." → "Movie Title"
        Skips teasers and "Coming Soon" announcements.

        Args:
            title (str): Video title

        Returns:
            str or None: Cleaned title, or None if invalid format
        """
        logger.debug(f"[MubiClient] Raw title: {title}")

        # Only process if it has "Official Trailer"
        if "Official Trailer" not in title or "Official Trailer #" in title:
            logger.debug(f"[MubiClient] Skipped (not a main trailer): {title}")
            return None

        # Extract everything before "Official Trailer" (remove pipes and whitespace)
        match = re.match(r"^(.+?)\s*\|\s*Official Trailer", title)
        if match:
            cleaned = match.group(1).strip()
            # Remove surrounding quotes
            cleaned = cleaned.strip("\"'")
            # Remove director's name pattern: "Director's TITLE" -> "TITLE"
            cleaned = re.sub(r"^[\w\s]+'s\s+", "", cleaned)
            # Convert to title case for better matching
            cleaned = cleaned.title()
            logger.debug(f"[MubiClient] Extracted title: {cleaned}")
            return cleaned if cleaned else None

        logger.debug(f"[MubiClient] Regex failed to match: {title}")
        return None

    def get_videos(self):
        """Fetch videos from Mubi channel."""
        return self.get_data()


class A24Client(YouTubeBaseClient):
    """
    A24 channel client.

    Handles A24-specific title format.
    A24 titles are either plain ("Materialists") or pipe-separated
    ("Undertone | Official Trailer 2 HD | A24").
    """

    CHANNEL_URL = "https://www.youtube.com/@A24/videos"
    CHANNEL_ID = "UCuPivVjnfNo4mb3Oog_frZg"

    def _clean_title(self, title):
        """
        Extract movie title from A24 title format.

        Formats:
          - "Materialists" → "Materialists"
          - "Undertone | Official Trailer HD | A24" → "Undertone"

        Skips anything that has not "Official Trailer HD".

        Args:
            title (str): Video title

        Returns:
            str or None: Cleaned title, or None if invalid format
        """
        logger.debug(f"[A24Client] Raw title: {title}")

        if "Official Trailer HD" not in title:
            return None

        # Take everything before the first pipe
        cleaned = title.split("|")[0].strip()

        # Remove surrounding quotes
        cleaned = cleaned.strip("\"'")

        # Convert to title case
        cleaned = cleaned.title()

        logger.debug(f"[A24Client] Extracted title: {cleaned}")
        return cleaned if cleaned else None

    def get_videos(self):
        """Fetch videos from A24 channel."""
        return self.get_data()


class NeonClient(YouTubeBaseClient):
    """
    Neon channel client.

    Handles Neon-specific title format.
    Neon titles are dash-separated
    ("I LOVE BOOSTERS - Official Trailer - Only In Theaters May 22").
    """

    CHANNEL_URL = "https://www.youtube.com/@neonrated/videos"
    CHANNEL_ID = "UCpy5dRhZd-JbZP4NsrnLt1w"

    def _clean_title(self, title):
        """
        Extract movie title from A24 title format.

        Formats:
          - "I LOVE BOOSTERS - Official Trailer - Only In Theaters May 22" → "I love boosters"

        Skips anything that has not "Official Trailer".

        Args:
            title (str): Video title

        Returns:
            str or None: Cleaned title, or None if invalid format
        """
        logger.debug(f"[NeonClient] Raw title: {title}")

        # Only process if it has "Official Trailer"
        if "Official Trailer" not in title or "Official Trailer #" in title:
            logger.debug(f"[NeonClient] Skipped (not a main trailer): {title}")
            return None

        # Take everything before the first pipe
        cleaned = title.split(" - ")[0].strip()

        # Remove surrounding quotes
        cleaned = cleaned.strip("\"'")

        # Convert to title case
        cleaned = cleaned.title()

        logger.debug(f"[NeonClient] Extracted title: {cleaned}")
        return cleaned if cleaned else None

    def get_videos(self):
        """Fetch videos from Neon channel."""
        return self.get_data()
