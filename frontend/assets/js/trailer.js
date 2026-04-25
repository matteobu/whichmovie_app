(function() {
    'use strict';

    var overlay = document.getElementById('yt-overlay');
    var closeBtn = document.getElementById('yt-overlay-close');
    var player = null;
    var currentVideoId = null;
    var apiReady = false;

    // Load YouTube IFrame API
    var tag = document.createElement('script');
    tag.src = 'https://www.youtube.com/iframe_api';
    document.head.appendChild(tag);

    window.onYouTubeIframeAPIReady = function() {
        apiReady = true;
    };

    function openTrailer(videoId) {
        if (!videoId) return;
        currentVideoId = videoId;
        overlay.classList.add('active');
        document.body.style.overflow = 'hidden';

        if (player) {
            player.destroy();
            player = null;
            // Re-create the target div (destroy removes it)
            var wrapper = document.querySelector('.yt-embed-wrapper');
            var div = document.createElement('div');
            div.id = 'yt-player';
            wrapper.appendChild(div);
        }

        createPlayer(videoId);
    }

    function createPlayer(videoId) {
        if (!apiReady) {
            setTimeout(function() { createPlayer(videoId); }, 100);
            return;
        }
        player = new YT.Player('yt-player', {
            videoId: videoId,
            playerVars: { autoplay: 1, rel: 0, modestbranding: 1 },
            events: {
                onError: function(e) {
                    // 101 / 150 = embedding disabled by video owner
                    if (e.data === 101 || e.data === 150) {
                        closeTrailer();
                        window.open('https://www.youtube.com/watch?v=' + currentVideoId, '_blank');
                    }
                }
            }
        });
    }

    function closeTrailer() {
        overlay.classList.remove('active');
        document.body.style.overflow = '';
        if (player) {
            player.stopVideo();
        }
    }

    closeBtn.addEventListener('click', closeTrailer);
    overlay.addEventListener('click', function(e) {
        if (e.target === overlay) closeTrailer();
    });
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && overlay.classList.contains('active')) closeTrailer();
    });

    document.addEventListener('click', function(e) {
        var btn = e.target.closest('button[data-video-id], a[data-video-id]');
        if (!btn) return;
        var videoId = btn.dataset.videoId;
        if (videoId) {
            e.preventDefault();
            openTrailer(videoId);
        }
    });

    window.openTrailer = openTrailer;
})();
