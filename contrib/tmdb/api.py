"""TMDB API client for fetching movie information."""

import logging
import re
from difflib import SequenceMatcher

import requests
from decouple import config

from contrib.base import BaseClient, NetworkError, ValidationError

logger = logging.getLogger(__name__)


def normalize_title(title):
    """Normalize a title for comparison."""
    if not title:
        return ""
    # Lowercase, remove special chars, extra spaces
    title = title.lower()
    title = re.sub(r"[^\w\s]", "", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title


def title_similarity(title1, title2):
    """Calculate similarity ratio between two titles (0.0 to 1.0)."""
    t1 = normalize_title(title1)
    t2 = normalize_title(title2)
    return SequenceMatcher(None, t1, t2).ratio()


def extract_year_from_title(title):
    """Extract year from title like 'Movie Name (2024)' or 'Movie Name 2024'."""
    if not title:
        return None
    # Match (2024) or [2024] at end of string
    match = re.search(r"[\(\[]?(19\d{2}|20\d{2})[\)\]]?\s*$", title)
    if match:
        return int(match.group(1))
    # Match year anywhere in title
    match = re.search(r"\b(19\d{2}|20\d{2})\b", title)
    if match:
        return int(match.group(1))
    return None


class TMDBClient(BaseClient):
    """
    TMDB (The Movie Database) API client.

    Fetches movie information from TMDB API v3.
    """

    BASE_URL = "https://api.themoviedb.org/3"

    def __init__(self, api_key=None):
        """
        Initialize TMDB client.

        Args:
            api_key (str, optional): TMDB API key. Defaults to TMDB_API_KEY env var.
        """
        self.api_key = api_key or config("TMDB_API_KEY", default=None)
        super().__init__()

    def _validate_config(self):
        """Validate that the client is properly configured."""
        if not self.api_key:
            raise ValidationError(
                "TMDB API key is required. Set TMDB_API_KEY environment variable."
            )

    def _make_request(self, endpoint, params=None):
        """
        Make a request to TMDB API.

        Args:
            endpoint (str): API endpoint (e.g., '/search/movie')
            params (dict, optional): Query parameters

        Returns:
            dict: API response data

        Raises:
            NetworkError: If request fails
        """
        if params is None:
            params = {}

        # Add API key to params
        params["api_key"] = self.api_key

        try:
            url = f"{self.BASE_URL}{endpoint}"
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"TMDB API request failed: {e}") from e

    # Minimum similarity threshold to accept a match
    MIN_SIMILARITY_THRESHOLD = 0.6

    def search_movie(self, title, year=None, min_similarity=None):
        """
        Search for a movie by title with smart matching.

        Searches TMDB and finds the best match based on:
        - Title similarity scoring
        - Year matching (if provided)

        Args:
            title (str): Movie title to search for
            year (int, optional): Release year to narrow search
            min_similarity (float, optional): Minimum similarity threshold (0.0-1.0)

        Returns:
            dict or None: Movie data if found with sufficient confidence, None otherwise

        Movie data includes:
            - id: TMDB ID
            - title: Movie title
            - release_date: Release date (YYYY-MM-DD)
            - overview: Movie description
            - poster_path: Poster image path
            - backdrop_path: Backdrop image path
            - imdb_id: IMDb ID (requires external_ids endpoint)
            - match_score: Confidence score of the match
        """
        if min_similarity is None:
            min_similarity = self.MIN_SIMILARITY_THRESHOLD

        try:
            # Try to extract year from title if not provided
            extracted_year = extract_year_from_title(title)
            search_year = year or extracted_year

            # Clean title for search (remove year if present)
            clean_title = re.sub(
                r"\s*[\(\[]?(19\d{2}|20\d{2})[\)\]]?\s*$", "", title
            ).strip()

            params = {
                "query": clean_title,
                "include_adult": False,
            }

            if search_year:
                params["year"] = search_year

            # Search for the movie
            response = self._make_request("/search/movie", params)

            if not response.get("results"):
                # Retry without year if no results
                if search_year:
                    logger.info(
                        f"No results for '{clean_title}' ({search_year}), retrying without year..."
                    )
                    del params["year"]
                    response = self._make_request("/search/movie", params)

            if not response.get("results"):
                logger.info(f"No results found for '{title}'")
                return None

            # Find best match by scoring all results
            best_match = None
            best_score = 0

            for result in response["results"][:5]:  # Check top 5 results
                result_title = result.get("title", "")
                result_year = None
                if result.get("release_date"):
                    try:
                        result_year = int(result["release_date"][:4])
                    except (ValueError, TypeError):
                        pass

                # Calculate title similarity
                sim_score = title_similarity(clean_title, result_title)

                # Boost score if year matches
                if search_year and result_year:
                    if search_year == result_year:
                        sim_score = min(
                            1.0, sim_score + 0.2
                        )  # Boost for exact year match
                    elif abs(search_year - result_year) <= 1:
                        sim_score = min(1.0, sim_score + 0.1)  # Small boost for ±1 year

                if sim_score > best_score:
                    best_score = sim_score
                    best_match = result

            # Check if best match meets threshold
            if best_match and best_score >= min_similarity:
                # Try to get IMDb ID (requires additional request)
                imdb_id = self._get_imdb_id(best_match["id"])
                best_match["imdb_id"] = imdb_id
                best_match["match_score"] = best_score

                logger.info(
                    f"Found movie: {best_match.get('title')} (TMDB ID: {best_match.get('id')}, "
                    f"score: {best_score:.2f})"
                )
                return best_match
            else:
                logger.warning(
                    f"No confident match for '{title}' (best score: {best_score:.2f} < {min_similarity})"
                )
                return None

        except NetworkError as e:
            logger.error(f"Error searching for '{title}': {e}")
            raise

    def _get_imdb_id(self, tmdb_id):
        """
        Get IMDb ID from TMDB movie ID.

        Args:
            tmdb_id (int): TMDB movie ID

        Returns:
            str or None: IMDb ID if found, None otherwise
        """
        try:
            response = self._make_request(f"/movie/{tmdb_id}/external_ids")
            return response.get("imdb_id")
        except NetworkError as e:
            logger.warning(f"Could not fetch IMDb ID for TMDB ID {tmdb_id}: {e}")
            return None

    def get_movie_details(self, tmdb_id):
        """
        Get full movie details from TMDB.

        Args:
            tmdb_id (int): TMDB movie ID

        Returns:
            dict or None: Full movie details including runtime, genres, etc.
        """
        try:
            response = self._make_request(
                f"/movie/{tmdb_id}",
                params={"append_to_response": "watch/providers"},
            )

            # Extract genre names from genre objects
            genres = [g["name"] for g in response.get("genres", [])]

            # Extract production country codes
            production_countries = [
                c["iso_3166_1"] for c in response.get("production_countries", [])
            ]

            providers_results = response.get("watch/providers", {}).get("results", {})
            watch_providers = {
                country: {
                    "flatrate": [
                        {"name": p["provider_name"], "logo": p["logo_path"]}
                        for p in data.get("flatrate", [])
                    ],
                    "link": data.get("link"),
                }
                for country, data in providers_results.items()
            }
            return {
                "id": response.get("id"),
                "title": response.get("title"),
                "overview": response.get("overview"),
                "release_date": response.get("release_date"),
                "poster_path": response.get("poster_path"),
                "backdrop_path": response.get("backdrop_path"),
                "genres": genres,
                "vote_average": response.get("vote_average"),
                "vote_count": response.get("vote_count"),
                "runtime": response.get("runtime"),
                "popularity": response.get("popularity"),
                "original_language": response.get("original_language"),
                "production_countries": production_countries,
                "watch_providers": watch_providers,
            }
        except NetworkError as e:
            logger.error(f"Error fetching movie details for TMDB ID {tmdb_id}: {e}")
            return None

    def get_data(self, **kwargs):
        """
        Fetch data from TMDB API.

        Args:
            **kwargs: API-specific parameters (query, year, etc.)

        Returns:
            dict: Movie data from TMDB
        """
        title = kwargs.get("query") or kwargs.get("title")
        year = kwargs.get("year")

        if not title:
            raise ValidationError("'title' or 'query' parameter is required")

        return self.search_movie(title, year)
