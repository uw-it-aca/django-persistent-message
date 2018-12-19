/*jslint browser: true, plusplus: true */
/*global jQuery, Handlebars, moment */
(function ($) {
    'use strict';

    var transition_tmpl = Handlebars.compile($('#transition-tmpl').html());

    function transition() {
        $('#pm-content').html(transition_tmpl());
    }

    function format_date(date_str) {
        return moment(date_str).format("MMMM D[,] YYYY [at] h:mm A");
    }

    Handlebars.registerHelper('format_date', function(date_str) {
        return format_date(date_str);
    });

    Handlebars.registerHelper('if_equals', function(arg1, arg2, options) {
        return (arg1 === arg2) ? options.fn(this) : options.inverse(this);
    });

    Handlebars.registerHelper('lower', function(str) {
        return str.toLowerCase();
    });

    $(document).ready(function () {
        $.ajaxSetup({
            crossDomain: false,
            beforeSend: function (xhr, settings) {
                if (window.persistent_message.session_id) {
                    xhr.setRequestHeader('X-SessionId',
                                         window.persistent_message.session_id);
                }
                if (!/^(GET|HEAD|OPTIONS|TRACE)$/.test(settings.type)) {
                    xhr.setRequestHeader('X-CSRFToken',
                                         window.persistent_message.csrftoken);
                }
                transition();
            }
        });

        function cache_tag_groups(data) {
            window.persistent_message.tag_groups = data.tag_groups;
        }

        function init_tag_groups(callback) {
            $.ajax({
                url: window.persistent_message.tags_api,
                dataType: 'json',
            }).fail().done(cache_tag_groups).done(callback);
        }

        function get_message() {
            return $.ajax({
                url: window.persistent_message.message_api,
                dataType: 'json'
            });
        }

        function get_messages() {
            return $.ajax({
                url: window.persistent_message.message_api,
                dataType: 'json'
            });
        }

        function delete_error(xhr) {
            var data;
            try {
                data = $.parseJSON(xhr.responseText);
            } catch (e) {
                data = {error: xhr.responseText};
            }
            alert('Delete failed: ' + data.error);
        }

        function delete_message() {
            /*jshint validthis: true */
            var message_id = $(this).attr('id').replace('message-', '');

            if (message_id.match(/^[0-9]+$/)) {
                if (confirm('Delete this message?')) {
                    $.ajax({
                        url: window.persistent_messsage.message_api + '/' + message_id,
                        dataType: 'json',
                        type: 'DELETE'
                    }).fail(delete_error).done(load_messages);
                }
            }
        }

        function add_message() {
            var content = $.trim($("textarea[name='content']").val());

            $.ajax({
                url: window.persistent_message.message_api,
                dataType: 'json',
                contentType: 'application/json',
                type: 'POST',
                data: JSON.stringify({content: content})
            }).fail(load_form).done(load_confirmation);
        }

        function update_message() {
            var description = $.trim($("textarea[name='description']").val()),
                name = $.trim($("input[name='name']").val());

            $.ajax({
                url: window.persistent_message.message_api,
                dataType: 'json',
                contentType: 'application/json',
                type: 'PUT',
                data: JSON.stringify({name: name, description: description})
            }).fail(load_form).done(init_form);
        }

        function load_confirmation(data) {
            var template = Handlebars.compile($('#confirmation-tmpl').html());
            $('#pm-content').html(template(data));
            $('#pm-header').html(data.name);
        }

        function load_form(data) {
            var template = Handlebars.compile($('#message-form-tmpl').html());
            data.tag_groups = window.persistent_message.tag_groups;
            data.message_levels = window.persistent_message.message_levels;
            $('#pm-content').html(template(data));
            //$('#pm-header').html(data.name);
            $('button.pm-btn-submit').click(add_message);
            $('#pm-message-content').focus();
        }

        function load_messages(data) {
            var template = Handlebars.compile($('#message-list-tmpl').html());
            data.tag_groups = window.persistent_message.tag_groups;
            $('#pm-content').html(template(data));
            $('#pm-header').html('Messages');
            //$('a.pm-btn-publish').click(publish_message);
            $('a.pm-btn-delete').click(delete_message);
        }

        function load_error(xhr) {
            var data, template, source;
            try {
                data = $.parseJSON(xhr.responseText);
            } catch (e) {
                data = {error: xhr.responseText};
            }
            source = $("#" + xhr.status + '-tmpl').html();
            if (source) {
                template = Handlebars.compile(source);
                $('#pm-content').html(template(data));
            }
        }

        function init_messages() {
            $('#pm-messages-link').tab('show');
            get_messages().fail(load_error).done(load_messages);
        }

        function init_add_message() {
            var data = {'message': {}};
            $('#pm-message-add-link').tab('show');
            load_form(data);
        }

        function initialize() {
            $('#pm-message-add-link').click(init_add_message);
            $('#pm-messages-link').click(init_messages);
            init_tag_groups(init_messages);
        }

        initialize();
    });
}(jQuery));
