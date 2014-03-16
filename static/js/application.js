jQuery(document).ready(function($){
    //------------------------------ PREVIOUS MOOD NAVIGATION
    $('#previous-mood-time-previous').on('click', function(){
        if (!$(this).hasClass('disabled')) change_mood('previous');
    });

    $('#previous-mood-time-next').on('click', function(){
        if (!$(this).hasClass('disabled')) change_mood('next');
    });

    function change_mood(direction) {
        var active = $('.previous-mood-panel.active');
        if (direction == 'previous') {
            var show = active.prev('.previous-mood-panel');
        } else {
            var show = active.next('.previous-mood-panel');
        }
        active.removeClass('active').addClass('hide');
        show.removeClass('hide').addClass('active');

        $('#previous-mood-time').find('time').text(show.data('time'));

        if (show.next('.previous-mood-panel').length) {
            $('#previous-mood-time-next').removeClass('disabled');
        } else {
            $('#previous-mood-time-next').addClass('disabled');
        }

        if (show.prev('.previous-mood-panel').length) {
            $('#previous-mood-time-previous').removeClass('disabled');
        } else {
            $('#previous-mood-time-previous').addClass('disabled');
        }

    }
    //----------------------- END PREVIOUS MOOD NAVIGATION
    //----------------------- MOOD SLIDER COLORING
    $('input[type="range"]').change(function () {
        var val = ($(this).val() - $(this).attr('min')) / ($(this).attr('max') - $(this).attr('min'));

        if (val > 0.75) {
            var color = "#5cb85c";
        } else if (val > 0.5) {
            var color = "#f0ad4e";
        } else {
            var color = "#d9534f";
        }

        $(this).css('background-image',
            '-webkit-gradient(linear, left top, right top, '
                + 'color-stop(' + val + ', ' + color + '), '
                + 'color-stop(' + val + ', #C5C5C5)'
                + ')'
        );
    });
    //----------------------- END MOOD SLIDER COLORING
    //----------------------- POPOVER
    $('.navigation h1[data-toggle=popover]').popover({
        trigger: 'hover',
        container: 'body',
        placement: 'bottom'
    });
    $('#section-calendar a').popover({
        trigger: 'hover',
        container: 'body',
        html: 'true',
        content: function() {
            var elem = $(this);
            var location = elem.data('location').trim();
            var description = elem.data('description').trim();

            var content = "";
            if (description) {
                content += description;
            }

            if (location && content) {
                content += "<br><br>";
            }

            if (location) {
                content += "<strong>Location</strong><br>" + location;
            }

            return content;
        }
    });
    //----------------------- END POPOVER


});