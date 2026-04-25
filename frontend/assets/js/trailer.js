(function() {
    'use strict';

    const overlay = document.getElementById('yt-overlay');
    const iframe = document.getElementById('yt-iframe');
    const closeBtn = document.getElementById('yt-overlay-close');

    function openTrailer(videoId) {
        if (!videoId) return;
        iframe.src = 'https://www.youtube.com/embed/' + videoId + '?autoplay=1&rel=0';
        overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeTrailer() {
        overlay.classList.remove('active');
        iframe.src = '';
        document.body.style.overflow = '';
    }

    closeBtn.addEventListener('click', closeTrailer);
    overlay.addEventListener('click', function(e) {
        if (e.target === overlay) closeTrailer();
    });
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && overlay.classList.contains('active')) closeTrailer();
    });

    document.addEventListener('click', function(e) {
        const btn = e.target.closest('[data-video-id]');
        if (!btn) return;
        const videoId = btn.dataset.videoId;
        if (videoId) {
            e.preventDefault();
            openTrailer(videoId);
        }
    });

    window.openTrailer = openTrailer;
})();
