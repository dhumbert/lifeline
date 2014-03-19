jQuery(document).ready(function($){
    //------------------------------ PREVIOUS MOOD ACTIVATION
    var previousMoods = $('.previous-mood-panel');
    if (previousMoods.length) {
        var last = previousMoods.last();
        last.removeClass('hide').addClass('active');
        $('#previous-mood-time').find('time').text(last.data('time'));
        $('#previous-moods').removeClass('hide');
        if (previousMoods.length > 1) {
            $('#previous-mood-time-previous').removeClass('disabled');
        }
    }
    //------------------------------ END PREVIOUS MOOD ACTIVATION
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
    //----------------------- SAVE ALL
    $('#form-sections').on('submit', function(){
        var save_btn = $('#save-btn');
        save_btn.attr('disabled', 'disabled');

        var save_btn_label = $('#save-btn-label');
        save_btn_label.text("Saving...");

        $.post('/ajax/save', $(this).serialize(), function(){
            save_btn.removeAttr('disabled');
            save_btn_label.text("Save");

        });

        return false;
    });
    //----------------------- END SAVE ALL
    //----------------------- SAVE MOOD
    $('#form-mood').on('submit', function(){
        var save_btn = $('#save-mood-btn');
        save_btn.attr('disabled', 'disabled');

        var save_btn_label = $('#save-mood-btn-label');
        save_btn_label.text("Saving...");

        $.post('/ajax/save-mood', $(this).serialize(), function(){
            save_btn.removeAttr('disabled');
            save_btn_label.text("Save Mood");

        });

        return false;
    });
    //----------------------- END SAVE MOOD
    //----------------------- SETTINGS FORM
    $('#settingsForm').on('submit', function(){
        $.post('/ajax/save-settings', $(this).serialize(), function(){
            document.location.reload();
        });
        return false;
    });
    //----------------------- END SETTINGS FORM
    //----------------------- AUTOSAVE
//    setInterval(function(){
//        $('#form-sections').submit();
//    }, 60 * 1000); // autosave every 60 seconds
    //----------------------- END AUTOSAVE


});