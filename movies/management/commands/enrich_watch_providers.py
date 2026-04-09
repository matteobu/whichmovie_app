import logging

from django.core.management.base import BaseCommand

from contrib.base import NetworkError
from contrib.tmdb.api import TMDBClient
from movies.models import Movie

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Enrich Movie objects that have no watch provider data using TMDB."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Maximum number of movies to process (default: all).",
        )

    def handle(self, *args, **options):
        qs = Movie.objects.filter(watch_providers={}, tmdb_id__isnull=False)
        limit = options["limit"]
        if limit:
            qs = qs[:limit]

        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS("No movies need enrichment."))
            return

        self.stdout.write(f"Enriching {total} movie(s)...")

        client = TMDBClient()
        updated = 0
        failed = 0

        for movie in qs.iterator():
            try:
                details = client.get_movie_details(movie.tmdb_id)
                if details is None:
                    self.stderr.write(
                        self.style.WARNING(
                            f"[SKIP] '{movie.title}' (tmdb_id={movie.tmdb_id}): no data returned."
                        )
                    )
                    failed += 1
                    continue

                watch_providers = details.get("watch_providers") or {}
                movie.watch_providers = watch_providers
                movie.save(update_fields=["watch_providers", "updated_at"])
                updated += 1
                logger.info(
                    "Enriched '%s' (tmdb_id=%s): %d country/ies.",
                    movie.title,
                    movie.tmdb_id,
                    len(watch_providers),
                )
                self.stdout.write(
                    f"  [OK] '{movie.title}' — {len(watch_providers)} country/ies."
                )

            except NetworkError as exc:
                failed += 1
                logger.error(
                    "Network error for '%s' (tmdb_id=%s): %s",
                    movie.title,
                    movie.tmdb_id,
                    exc,
                )
                self.stderr.write(
                    self.style.ERROR(
                        f"  [FAIL] '{movie.title}' (tmdb_id={movie.tmdb_id}): {exc}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone. Updated: {updated}, Failed/skipped: {failed}, Total: {total}."
            )
        )
