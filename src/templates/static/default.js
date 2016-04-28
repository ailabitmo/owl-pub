jQuery(document).ready(function ($) {
    /* Sticky sidebar ("Table of contents") */
    $(".sticky").sticky({topSpacing: 10});

    /* Branches switcher */
    $("#branch_switcher").change(function () {
        window.location.href = $(this).val();
    });

    /* Scroll to anchor */
    jQuery('a[href^="#"]').click(function (event) {
        event.preventDefault();
        jQuery('html, body').animate({
            scrollTop: jQuery('#' + jQuery(this).attr('href').substring(1)).offset().top
        }, 500);
    });

    /* Find broken anchors */
    jQuery('a[href^="#"]').each(function () {
        if (jQuery('#' + jQuery(this).attr('href').substring(1)).length == 0) {
            jQuery(this).css('color', 'red');
        }
    });
});
