/*jslint browser: true, plusplus: true */
/*global jQuery, Handlebars, moment */
(function ($) {
    'use strict';

    var transition_tmpl = Handlebars.compile($('#transition-tmpl').html());

    function transition() {
        $('#pm-content').html(transition_tmpl());
    }

    function format_date(date_str) {
        var dt = moment(date_str);
        if (dt.isValid()) {
            return dt.format('MMM[.] D[,] YYYY[,] h:mm A');
        }
        return '';
    }

    Handlebars.registerHelper('format_date', function(date_str) {
        return format_date(date_str);
    });

    Handlebars.registerHelper('if_equals', function(arg1, arg2, options) {
        return (arg1 === arg2) ? options.fn(this) : options.inverse(this);
    });

    Handlebars.registerHelper('has_tag', function(tags, name, options) {
        for (var i = 0; i < tags.length; i++)  {
            if (name === tags[i].name) {
                return options.fn(this);
            }
        }
        return options.inverse(this);
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

        function get_message(message_id) {
            return $.ajax({
                url: window.persistent_message.message_api + '/' + message_id,
                dataType: 'json'
            });
        }

        function get_messages() {
            return $.ajax({
                url: window.persistent_message.message_api,
                dataType: 'json'
            });
        }

        function ajax_error(xhr) {
            var data;
            try {
                data = $.parseJSON(xhr.responseText);
            } catch (e) {
                data = {error: xhr.responseText};
            }
            alert(xhr.method + ' failed: ' + data.error);
        }

        function delete_message() {
            /*jshint validthis: true */
            var message_id = $(this).attr('id').replace('pm-delete-', ''),
                confirmation = 'Delete this message?';

            if (message_id.match(/^[0-9]+$/)) {
                if (confirm(confirmation)) {
                    $.ajax({
                        url: window.persistent_message.message_api + '/' + message_id,
                        dataType: 'json',
                        type: 'DELETE'
                    }).fail(ajax_error).done(init_messages);
                }
            }
        }

        function toggle_publish_message() {
            /*jshint validthis: true */
            var message_id = $(this).attr('id').replace('pm-publish-', ''),
                message = window.persistent_message.messages[message_id],
                now = moment().subtract(5, 'seconds'),
                confirmation,
                data = {};

            if ($(this).hasClass('pm-btn-publish')) {
                data.begins = now.utc().toISOString();
                confirmation = 'Publish this message?';
                if (message.expires !== null && moment(message.expires).isBefore(now)) {
                    data.expires = null;
                    confirmation += ' Expiration will be set to "Never".';
                }
            } else {
                data.expires = now.utc().toISOString();
                confirmation = 'Unpublish this message?';
            }

            if (confirm(confirmation)) {
                $.ajax({
                    url: window.persistent_message.message_api + '/' + message_id,
                    dataType: 'json',
                    contentType: 'application/json',
                    type: 'PUT',
                    data: JSON.stringify({'message': data})
                }).fail(ajax_error).done(init_messages);
            }
        }

        function _serialize_form() {
            /*jshint loopfunc: true */
            var data = {},
                begins = $.trim($('input[name="begins"]').val()),
                expires = $.trim($('input[name="expires"]').val()),
                tag_groups_len = window.persistent_message.tag_groups.length,
                group_tags,
                group_name,
                i;

            data.content = $.trim($('textarea[name="content"]').val());
            data.level = $('input[name="level"]:checked').val();
            data.tags = [];
            data.begins = null;
            data.expires = null;

            for (i = 0; i < tag_groups_len; i++)  {
                group_name = window.persistent_message.tag_groups[i].name.toLowerCase();
                group_tags = $('input[name="tag_' + group_name + '"]:checked').map(
                    function () { return $(this).val(); }).get();
                data.tags.push.apply(data.tags, group_tags);
            }

            if (begins !== null && begins.length) {
                begins = moment(begins, 'L LT');
                if (begins.isValid()) {
                    data.begins = begins.utc().toISOString();
                }
            }

            if (expires !== null && expires.length) {
                expires = moment(expires, 'L LT');
                if (expires.isValid()) {
                    data.expires = expires.utc().toISOString();
                }
            }

            return JSON.stringify({'message': data});
        }

        function add_message() {
            var post_data = _serialize_form();
            $.ajax({
                url: window.persistent_message.message_api,
                dataType: 'json',
                contentType: 'application/json',
                type: 'POST',
                data: post_data
            }).fail(load_form).done(init_messages);
        }

        function update_message() {
            var message_id = $('input[name="message_id"]').val(),
                put_data = _serialize_form();

            $.ajax({
                url: window.persistent_message.message_api + '/' + message_id,
                dataType: 'json',
                contentType: 'application/json',
                type: 'PUT',
                data: put_data
            }).fail(load_form).done(init_messages);
        }

        function load_form(data) {
            var template = Handlebars.compile($('#message-form-tmpl').html()),
                now = moment(),
                begins = (data.message.begins) ? moment(data.message.begins) : now,
                expires = (data.message.expires) ? moment(data.message.expires) : null;
            data.tag_groups = window.persistent_message.tag_groups;
            data.message_levels = window.persistent_message.message_levels;
            $('#pm-content').html(template(data));

            $('#pm-begins-datetimepicker').datetimepicker({
                locale: 'en',
                format: 'L LT',
                minDate: (begins.isBefore(now)) ? begins : now,
                defaultDate: begins
            }).on('dp.change', function (e) {
                var expires_dtp = $('#pm-expires-datetimepicker').data('DateTimePicker'),
                    expires = expires_dtp.date();
                expires_dtp.minDate(e.date);
                if (expires === null) {
                    expires_dtp.date(expires);
                }
            });
            $('#pm-expires-datetimepicker').datetimepicker({
                locale: 'en',
                format: 'L LT',
                minDate: (expires === null) ? begins : false,
                defaultDate: (expires !== null) ? expires : false
            });
            $('button.pm-btn-submit').click((data.message.id) ? update_message : add_message);
            $('button.pm-btn-cancel').click(init_messages);
            $('#pm-message-content').focus();
        }

        function load_messages(data) {
            var template = Handlebars.compile($('#message-list-tmpl').html()),
                i;
            data.tag_groups = window.persistent_message.tag_groups;
            $('#pm-content').html(template(data));
            $('button.pm-btn-edit').click(init_edit_message);
            $('button.pm-btn-publish, button.pm-btn-unpublish').click(toggle_publish_message);
            $('button.pm-btn-delete').click(delete_message);

            window.persistent_message.messages = {};
            for (i = 0; i < data.messages.length; i++)  {
                window.persistent_message.messages[data.messages[i].id] = data.messages[i];
            }
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

        function init_edit_message() {
            /*jshint validthis: true */
            var message_id = $(this).attr('id').replace('pm-edit-', '');
            $('#pm-message-add-link').tab('show');
            get_message(message_id).fail(load_error).done(load_form);
        }

        function init_add_message() {
            var data = {'message': {level: 20, tags: []}};
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
