$(document).ready(function() {
    var navbar = $('#mainNavbar');
    var scrollThreshold = 50; // Pixels to scroll before change

    $(window).scroll(function() {
        if ($(window).scrollTop() > scrollThreshold) {
            // User has scrolled down
            navbar.removeClass('navbar-transparent').addClass('navbar-scrolled');
        } else {
            // User is at the top
            navbar.addClass('navbar-transparent').removeClass('navbar-scrolled');
        }
    });

    // FILTER LOGIC
    $('.btn-filter').click(function() {
        // 1. Visual Update
        $('.btn-filter').removeClass('active btn-primary text-white').addClass('btn-light');
        $(this).removeClass('btn-light').addClass('active btn-primary text-white');
        
        var sportId = $(this).data('filter');

        // 2. AJAX Request
        $.ajax({
            url: '/api/filter_events',
            type: 'POST',
            data: { sport_id: sportId },
            beforeSend: function() {
                // Optional: Add a loading opacity effect
                $('#events-grid').css('opacity', '0.5');
            },
            success: function(response) {
                // 3. Update DOM with new HTML
                $('#events-grid').html(response.html).css('opacity', '1');
                
                // Re-initialize animations if using AOS
                if(typeof AOS !== 'undefined'){
                    AOS.refresh(); 
                }
            },
            error: function(xhr, status, error) {
                console.error("Error:", error);
                alert("Failed to load events. Check console for details.");
                $('#events-grid').css('opacity', '1');
            }
        });
    });


    // EVENT DETAILS MODAL LOGIC
    $(document).on('click', '.btn-details', function() {
        var eventId = $(this).data('event-id');
        var modal = new bootstrap.Modal(document.getElementById('globalEventModal'));
        var contentContainer = $('#globalEventModal .modal-content');
        
        // 1. Show Modal with Loading Spinner first
        contentContainer.html(`
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status"></div>
                <p class="mt-2 text-muted">Loading event details...</p>
            </div>
        `);
        modal.show();

        // 2. Fetch Details via AJAX
        $.ajax({
            url: '/api/get_event_details',
            type: 'POST',
            data: { event_id: eventId },
            success: function(response) {
                // 3. Inject Content
                contentContainer.html(response.html);
            },
            error: function() {
                contentContainer.html(`
                    <div class="p-4 text-center text-danger">
                        <i class="fas fa-exclamation-triangle fa-2x mb-2"></i>
                        <p>Failed to load details. Please try again.</p>
                        <button class="btn btn-light btn-sm" data-bs-dismiss="modal">Close</button>
                    </div>
                `);
            }
        });
    });


// 1. FILTER LOGIC (Auto-submit on change)
$('.filter-input').on('change keyup', function() {
    // Debounce search slightly
    clearTimeout(window.filterTimeout);
    window.filterTimeout = setTimeout(() => {

        var formData = $('#filterForm').serialize();

        $.ajax({
            url: '/api/filter_events',
            type: 'POST',
            data: formData,
            beforeSend: function() {
                $('#events-grid').addClass('opacity-50');
                $('#gridLoader').removeClass('d-none');
            },
            success: function(response) {
                $('#events-grid').html(response.html).removeClass('opacity-50');
                $('#gridLoader').addClass('d-none');
            }
        });

    }, 300); // 300ms delay
});
// app/static/js/public/app.js

// Make the function global by attaching it to 'window'
window.toggleSave = function(eventId) {
    $.ajax({
        url: '/api/event/toggle_save',
        type: 'POST',
        data: { event_id: eventId },
        success: function(resp) {
            // Update the specific button clicked inside the modal
            var btn = $('#btnSaveEvent');
            var icon = btn.find('i');
            var text = btn.find('span');

            if(resp.action === 'saved') {
                btn.removeClass('btn-outline-danger').addClass('btn-danger');
                icon.removeClass('fa-heart-open').addClass('fa-heart');
                text.text('Following');

                // Optional: visual feedback
                showToast('success', 'Event added to your favorites!');
            } else {
                btn.removeClass('btn-danger').addClass('btn-outline-danger');
                icon.removeClass('fa-heart').addClass('fa-heart-open');
                text.text('Follow');

                showToast('info', 'Event removed from favorites.');
            }
        },
        error: function(xhr) {
            if(xhr.status === 401) {
                // If user is not logged in, redirect or alert
                window.location.href = '/auth/login';
            } else {
                alert("Error updating favorites.");
            }
        }
    });
};

// Helper Toast Function (if you don't have one yet)
function showToast(type, msg) {
    // You can use the Bootstrap toast container from previous steps
    // or a simple alert for now
    console.log(type + ": " + msg);
}











});
