document.addEventListener('DOMContentLoaded', function() {
    // Get CSRF token from cookie
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

    // Handle watchlist button clicks
    document.querySelectorAll('.watchlist-btn').forEach(function(btn) {
        btn.addEventListener('clicxk', function() {
            const movieId = this.dataset.movieId;
            const button = this;

            fetch('/movies/watchlist/toggle/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: 'movie_id=' + movieId
            })
            .then(response => response.json())
            .then(data => {
                if (data.added) {
                    button.classList.add('active');
                    button.title = 'Remove from Watchlist';
                } else {
                    button.classList.remove('active');
                    button.title = 'Add to Watchlist';
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    });
});
