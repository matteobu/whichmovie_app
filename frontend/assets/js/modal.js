(function() {
    'use strict';

    // Modal elements
    const modal = document.getElementById('movie-modal');
    const modalClose = document.getElementById('modal-close');
    const modalBackdrop = document.getElementById('modal-backdrop');
    const modalPoster = document.getElementById('modal-poster');
    const modalTitle = document.getElementById('modal-title');
    const modalMeta = document.getElementById('modal-meta');
    const modalGenres = document.getElementById('modal-genres');
    const modalOverview = document.getElementById('modal-overview');
    const modalTrailer = document.getElementById('modal-trailer');
    const modalWatchlist = document.getElementById('modal-watchlist');
    const modalProviders = document.getElementById('modal-providers');
    const modalProvidersCountry = document.getElementById('modal-providers-country');
    const modalProvidersList = document.getElementById('modal-providers-list');
const modalProvidersHeader = document.getElementById('modal-providers-header');

    let currentWatchProviders = {};

    let currentMovieId = null;

    // CSRF token helper
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Open modal with movie data
    function openMovieModal(movieData) {
        if (!modal) return;

        currentMovieId = movieData.id;

        // Set backdrop
        if (movieData.backdrop) {
            modalBackdrop.style.backgroundImage = 'url(https://image.tmdb.org/t/p/w780' + movieData.backdrop + ')';
        } else if (movieData.poster) {
            modalBackdrop.style.backgroundImage = 'url(https://image.tmdb.org/t/p/w780' + movieData.poster + ')';
        } else {
            modalBackdrop.style.backgroundImage = 'none';
            modalBackdrop.style.background = 'linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%)';
        }

        // Set poster
        if (movieData.poster) {
            modalPoster.src = 'https://image.tmdb.org/t/p/w342' + movieData.poster;
            modalPoster.alt = movieData.title;
            modalPoster.style.display = 'block';
        } else {
            modalPoster.style.display = 'none';
        }

        // Set title
        modalTitle.textContent = movieData.title || 'Unknown Title';

        // Set meta (year, rating, runtime)
        let metaHtml = '';
        if (movieData.year) {
            metaHtml += '<span class="modal-meta-item">' + movieData.year + '</span>';
        }
        if (movieData.rating && parseFloat(movieData.rating) > 0) {
            metaHtml += '<span class="modal-meta-item modal-rating">★ ' + parseFloat(movieData.rating).toFixed(1) + '</span>';
        }
        if (movieData.runtime && parseInt(movieData.runtime) > 0) {
            metaHtml += '<span class="modal-meta-item">' + movieData.runtime + ' min</span>';
        }
        modalMeta.innerHTML = metaHtml;

        // Set genres
        let genresHtml = '';
        if (movieData.genres) {
            const genreList = movieData.genres.split(',').filter(g => g.trim());
            genreList.forEach(function(genre) {
                genresHtml += '<span class="modal-genre">' + genre.trim() + '</span>';
            });
        }
        modalGenres.innerHTML = genresHtml;

        // Set overview
        modalOverview.textContent = movieData.overview || 'No overview available.';

        // Set trailer button
        if (movieData.videoId) {
            modalTrailer.href = 'https://www.youtube.com/watch?v=' + movieData.videoId;
            modalTrailer.style.display = 'inline-flex';
        } else {
            modalTrailer.style.display = 'none';
        }

        // Set watchlist button state
        const inWatchlist = movieData.inWatchlist === 'true' || movieData.inWatchlist === true;
        updateWatchlistButton(inWatchlist);

        // Set watch providers
        try {
            currentWatchProviders = movieData.watchProviders ? JSON.parse(movieData.watchProviders) : {};
        } catch (e) {
            currentWatchProviders = {};
        }
        renderProviders();

        // Show modal
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    // Render watch providers for the selected country
    function renderProviders() {
        if (!modalProviders) return;

        const countries = Object.keys(currentWatchProviders).filter(function(code) {
            return currentWatchProviders[code].flatrate && currentWatchProviders[code].flatrate.length > 0;
        });
        if (countries.length === 0) {
            modalProvidersHeader.style.display = 'none';
            modalProvidersList.innerHTML = '<span class="modal-providers-none">No available streaming.</span>';
            return;
        }

        modalProvidersHeader.style.display = '';
        modalProvidersList.style.display = 'flex';

        // Populate country selector (only on first render or when providers change)
        const userCountry = (navigator.language || 'en-US').split('-')[1] || 'US';
        const preferred = countries.includes(userCountry) ? userCountry : countries[0];

        if (modalProvidersCountry.dataset.populated !== 'true') {
            const regionNames = new Intl.DisplayNames([navigator.language || 'en'], { type: 'region' });
            modalProvidersCountry.innerHTML = '';
            countries.forEach(function(code) {
                const opt = document.createElement('option');
                opt.value = code;
                opt.textContent = regionNames.of(code) || code;
                if (code === preferred) opt.selected = true;
                modalProvidersCountry.appendChild(opt);
            });
            modalProvidersCountry.dataset.populated = 'true';
        }

        renderProviderList(modalProvidersCountry.value || preferred);
    }

    function renderProviderList(countryCode) {
        if (!modalProvidersList) return;
        const data = currentWatchProviders[countryCode];
        const flatrate = (data && data.flatrate) || [];

        if (flatrate.length === 0) {
            modalProvidersList.innerHTML = '<span class="modal-providers-none">Not available for streaming in this region.</span>';
            return;
        }

        modalProvidersList.innerHTML = flatrate.map(function(p) {
            const logo = p.logo ? 'https://image.tmdb.org/t/p/original' + p.logo : '';
            return logo
                ? '<div class="modal-provider"><img src="' + logo + '" alt="' + p.name + '" title="' + p.name + '"><span class="modal-provider-name">' + p.name + '</span></div>'
                : '<div class="modal-provider"><span class="modal-provider-name">' + p.name + '</span></div>';
        }).join('');
    }

    // Close modal
    function closeMovieModal() {
        if (!modal) return;
        modal.classList.remove('active');
        document.body.style.overflow = '';
        currentMovieId = null;
        currentWatchProviders = {};
        if (modalProvidersCountry) modalProvidersCountry.dataset.populated = '';
        modalProvidersList.style.display = 'block';
    }

    // Update watchlist button appearance
    function updateWatchlistButton(inWatchlist) {
        if (!modalWatchlist) return;
        const icon = modalWatchlist.querySelector('i');
        const text = modalWatchlist.querySelector('span');

        if (inWatchlist) {
            modalWatchlist.classList.add('active');
            if (text) text.textContent = 'In Watchlist';
        } else {
            modalWatchlist.classList.remove('active');
            if (text) text.textContent = 'Add to Watchlist';
        }
    }

    // Toggle watchlist
    function toggleWatchlist() {
        if (!currentMovieId) return;

        fetch('/movies/watchlist/toggle/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: 'movie_id=' + currentMovieId
        })
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            updateWatchlistButton(data.added);

            // Also update the card button if it exists
            const cardBtn = document.querySelector('.watchlist-btn[data-movie-id="' + currentMovieId + '"]');
            if (cardBtn) {
                if (data.added) {
                    cardBtn.classList.add('active');
                    cardBtn.title = 'Remove from Watchlist';
                } else {
                    cardBtn.classList.remove('active');
                    cardBtn.title = 'Add to Watchlist';
                }
            }

            // Update the card's data attribute
            const card = document.querySelector('[data-movie-id="' + currentMovieId + '"]');
            if (card && card.classList.contains('movie-card')) {
                card.dataset.inWatchlist = data.added ? 'true' : 'false';
            }
        })
        .catch(function(error) {
            console.error('Error toggling watchlist:', error);
        });
    }

    // Event listeners
    document.addEventListener('DOMContentLoaded', function() {
        // Close modal on close button click
        if (modalClose) {
            modalClose.addEventListener('click', closeMovieModal);
        }

        // Close modal on overlay click
        if (modal) {
            modal.addEventListener('click', function(e) {
                if (e.target === modal) {
                    closeMovieModal();
                }
            });
        }

        // Close modal on Escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && modal && modal.classList.contains('active')) {
                closeMovieModal();
            }
        });

        // Country selector for watch providers
        if (modalProvidersCountry) {
            modalProvidersCountry.addEventListener('change', function() {
                renderProviderList(this.value);
            });
        }

        // Watchlist button in modal
        if (modalWatchlist) {
            modalWatchlist.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();

                // Check if user is authenticated by checking for login redirect
                const loginLink = document.querySelector('a[href*="login_required"]');
                if (loginLink && !document.querySelector('.nav-btn-logout')) {
                    window.location.href = '/accounts/login-required/';
                    return;
                }

                toggleWatchlist();
            });
        }

        // Movie card click handlers
        document.addEventListener('click', function(e) {
            // Find the movie card (either .movie-card or .pick-card)
            const card = e.target.closest('.movie-card, .pick-card');

            if (!card) return;

            // Don't open modal if clicking on watchlist button, trailer link, or other interactive elements
            if (e.target.closest('.watchlist-btn, .remove-btn, .movie-link, a')) {
                return;
            }

            // Get movie data from data attributes
            const movieData = {
                id: card.dataset.movieId,
                title: card.dataset.title,
                overview: card.dataset.overview,
                poster: card.dataset.poster,
                backdrop: card.dataset.backdrop,
                year: card.dataset.year,
                rating: card.dataset.rating,
                runtime: card.dataset.runtime,
                genres: card.dataset.genres,
                videoId: card.dataset.videoId,
                inWatchlist: card.dataset.inWatchlist,
                watchProviders: card.dataset.watchProviders
            };

            // Only open if we have movie data
            if (movieData.id) {
                openMovieModal(movieData);
            }
        });
    });

    // Feedback modal elements
    const feedbackModal = document.getElementById('feedback-modal');
    const feedbackClose = document.getElementById('feedback-close');
    const feedbackForm = document.getElementById('feedback-form');
    const feedbackMovieInfo = document.getElementById('feedback-movie-info');
    const feedbackMovieId = document.getElementById('feedback-movie-id');
    const feedbackMovieTitle = document.getElementById('feedback-movie-title');
    const feedbackMessage = document.getElementById('feedback-message');
    const feedbackSubmit = document.getElementById('feedback-submit');
    const feedbackFormContainer = document.getElementById('feedback-form-container');
    const feedbackSuccess = document.getElementById('feedback-success');
    const modalFeedbackBtn = document.getElementById('modal-feedback');

    let currentMovieTitle = '';

    // Store movie title when modal opens
    const originalOpenMovieModal = openMovieModal;
    openMovieModal = function(movieData) {
        currentMovieTitle = movieData.title || 'Unknown Title';
        originalOpenMovieModal(movieData);
    };

    // Open feedback modal
    function openFeedbackModal() {
        if (!feedbackModal) return;

        feedbackMovieInfo.textContent = 'Movie: ' + currentMovieTitle;
        feedbackMovieId.value = currentMovieId;
        feedbackMovieTitle.value = currentMovieTitle;
        feedbackMessage.value = '';
        feedbackFormContainer.style.display = 'block';
        feedbackSuccess.style.display = 'none';
        feedbackModal.classList.add('active');
    }

    // Close feedback modal
    function closeFeedbackModal() {
        if (!feedbackModal) return;
        feedbackModal.classList.remove('active');
    }

    // Handle feedback form submission
    function submitFeedback(e) {
        e.preventDefault();

        const message = feedbackMessage.value.trim();
        if (!message) {
            feedbackMessage.focus();
            return;
        }

        feedbackSubmit.disabled = true;
        feedbackSubmit.textContent = 'Sending...';

        fetch('/movies/feedback/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: 'movie_id=' + encodeURIComponent(feedbackMovieId.value) +
                  '&movie_title=' + encodeURIComponent(feedbackMovieTitle.value) +
                  '&message=' + encodeURIComponent(message)
        })
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            if (data.success) {
                feedbackFormContainer.style.display = 'none';
                feedbackSuccess.style.display = 'block';
            } else {
                alert('Failed to send feedback. Please try again.');
            }
        })
        .catch(function(error) {
            console.error('Error:', error);
            alert('Failed to send feedback. Please try again.');
        })
        .finally(function() {
            feedbackSubmit.disabled = false;
            feedbackSubmit.textContent = 'Send Feedback';
        });
    }

    // Feedback event listeners
    if (modalFeedbackBtn) {
        modalFeedbackBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            openFeedbackModal();
        });
    }

    if (feedbackClose) {
        feedbackClose.addEventListener('click', closeFeedbackModal);
    }

    if (feedbackModal) {
        feedbackModal.addEventListener('click', function(e) {
            if (e.target === feedbackModal) {
                closeFeedbackModal();
            }
        });
    }

    if (feedbackForm) {
        feedbackForm.addEventListener('submit', submitFeedback);
    }

    // Close feedback modal on Escape
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && feedbackModal && feedbackModal.classList.contains('active')) {
            closeFeedbackModal();
        }
    });

    // Expose functions globally if needed
    window.openMovieModal = openMovieModal;
    window.closeMovieModal = closeMovieModal;
})();
