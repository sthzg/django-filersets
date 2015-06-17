(function ($) {

  /**
   * Make all of the table rows clickable to select/deselect the row
   */
  $('document').ready(function () {
    $('#result_list tbody tr').bind(
      'click',
      function () {
        var $cb = $(this).find('input.action-select');
        $cb.prop('checked', !$cb.prop("checked"));
        $(this).toggleClass('selected');
      });

    $('#result_list tbody tr a, ' +
      '#result_list tbody tr input,' +
      '#result_list tbody tr textarea').bind(
      'click', function (ev) {
        ev.stopPropagation();
      });
  });


  /**
   * UI band
   * -------
   * Widget container on the bottom of the screen that can hold arbitrary UI
   * elements/widgets like the Categorizr.
   *
   * The UI band is currently structured as a 3-split-container
   *
   * -----------------------------------------------------------------------------
   * | Widget Icons  |            Widget Display          |   Notification Area  |
   * -----------------------------------------------------------------------------
   *
   * Widget Icons:
   * Every registered widget is represented by an icon (clickable/tababble).
   *
   * Widget Display:
   * The currently active widget is displayed in this main area.
   *
   * Notification Area:
   * Features a queue in which time-based notifications could be added.
   *
   */
  var fs_uiband = {

    current_widget_id: undefined,
    $current_widget: undefined,

    $uib: undefined,
    $region_west: undefined,
    $region_middle: undefined,
    $region_east: undefined,

    widget_registry: {
      widgets: {}
    },

    /**
     * Returns the current UI band instance or creates it if it does not exist.
     *
     * @returns {*}
     */
    get_or_create: function () {

      if (this.$uib == undefined) {
        this.$uib_widget_menu = $('<ul class="uib-widget-menu"></ul>');
        this.$region_west = $('<div class="uib-region uib-region-west fs_iblock"></div>');
        this.$region_west.append(this.$uib_widget_menu);
        this.$region_middle = $('<div class="uib-region uib-region-middle fs_iblock"></div>');
        this.$region_middle_canvas = $('<div class="uib-middle-container"></div>');
        this.$region_middle.append(this.$region_middle_canvas);
        this.$region_east = $('<div class="uib-region  uib-region-east fs_iblock"></div>');
        this.$uib = $('<div class="uib-uiband"></div>');
        this.$uib.append(this.$region_west)
          .append(this.$region_middle)
          .append(this.$region_east);
      }
      return this.$uib;

    },

    /**
     * Show widget with id in the UI band.
     *
     * @param id
     */
    show_widget: function (id) {

      if (id == this.current_widget_id) {
        return;
      }

      $w = this.widget_registry.widgets[id];
      cur_idx = this.$current_widget.index();
      target_idx = $w.index();

      cur_y = parseInt(fs_uiband.$region_middle_canvas.css('margin-top'));
      offset = cur_y + (cur_idx - target_idx) * 30;
      this.$region_middle_canvas.stop().animate({
        'margin-top': offset + 'px'
      }, 160);

      this._set_current_widget(id);

    },

    /**
     * Adds $widget with id to the widget registry.
     *
     * @param id
     * @param $widget
     */
    register_widget: function (id, $widget) {

      // Check if the widget implements necessary settings.
      try {
        var controller = $widget.controller;
        var icon = $widget.controller.icon;
        var label = $widget.controller.label;
      } catch (err) {
        // TODO  Should link to documentation
        throw "Please provide a controller attribute on your widget and " +
        "configure icon and label.";
      }

      var that = this;

      $menu_item = $('<li class="uib-menu-item"></li>');
      $menu_item.append($('<i class="fa ' + icon + '" title="' + label + '"></i>'));
      $menu_item.attr('data-target', id);
      $menu_item.bind("click", function () {
        that.show_widget($(this).data('target'));
      });
      this.$uib_widget_menu.append($menu_item);

      $widget.addClass('uib-widget');
      $widget.attr('id', id);
      this.widget_registry.widgets[id] = $widget;
      this.$region_middle_canvas.append(this.widget_registry.widgets[id]);

      if (this.current_widget_id == undefined) {
        this._set_current_widget(id);
      }
    },


    remove_widget: function (id) {
      // TODO
    },

    /**
     * Sets quick access variables pointing to currently active widget.
     *
     * @param id
     * @private
     */
    _set_current_widget: function (id) {
      $('.uib-menu-item').removeClass('active');
      $('li[data-target="' + id + '"]').addClass('active');
      this.current_widget_id = id;
      this.$current_widget = this.widget_registry.widgets[id];
    }

  };


  /**
   * Categorizr
   * ----------
   * When rows are selected provide a widget inside the UI band that lets the
   * user batch assign the selected items to a category.
   */
  var fs_categorizr = {

    categories: undefined,
    cat_col_num: undefined,
    base_category: undefined,
    ui_lock: false,

    label: 'Categorizr',
    icon: 'fa-list',
    icon_type: 'fontawesome',   // TODO  Support fontawesome, PNG and SVG
    band_bgcolor: 'inherit',    // inherit or color value
    band_colormode: 'normal',   // normal or inverted

    $api: $(this),
    $uib: fs_uiband.get_or_create(),
    $cat_col: undefined,
    $categorizr: undefined,

    /**
     * Get the ``fs_categorizr`` instance. If it doesn't exist yet create it.
     *
     * @returns {*}
     */
    get_or_create: function (base_category) {
      this.base_category = base_category || undefined;

      if (this.$categorizr == undefined) {
        this.$api.bind('categories_ready', $.proxy(this.append_categories, this));
        this.get_categories(false);

        this.$categorizr = $('<div class="fs_categorizr_container"></div>');
        this.$categorizr.controller = this;
        this.cat_col_num = $('th.current_categories-column').prevAll().length + 1;
      }
      return this.$categorizr;
    },

    /**
     * Appends category buttons to categorizr.
     */
    append_categories: function () {
      var that = this;

      $ul = $('<ul class="categories"></ul>');
      $li = $('<li class="fs-inline-help">' +
        '<i class="fa fa-question-circle" title="Select one or more items ' +
        'in the list view and click on a category to assign that item to ' +
        'the list. (will not be duplicated if already included)"></i>' +
        '</li><li class="fs-feature-title">Categories</li>');
      $ul.append($li);

      // Build group select
      $li_select = $('<select class="fs-categorizr-group-select">');
      $.each(this.categories, function(key, val) {
        if (val.is_group) {
          $li_select.append(
            $('<option class="fs-categorizr-group-opt" value="' + val.slug_composed + '">' + val.name + '</option>')
          );
        }
      });
      $ul.append($('<li>').append($li_select));
      var current_group = $li_select.val();

      $li_select.on('change', function(ev) {
        $('.fs-categorizr-buttons').remove();
        $('ul.categories').append(that.render_buttons(this.value));
      });

      this.$categorizr.append($ul);

      $buttons = this.render_buttons(current_group);
      $ul.append($buttons);
    },

    render_buttons: function(current_group) {
      var that = this;
      var $buttons = [];

      $.each(this.categories, function (key, val) {
        if (
          val.slug_composed.indexOf(current_group) == -1 ||
          val.slug_composed == current_group
        ) {
          return;
        }

        $li = $('<li class="fs_category_item"></li>');
        $atag = $('<a href="#" data-pk="' + val.id + '"></a>');
        $alabel = $atag.append(val.name);

        //                                                                     ___
        //                                                             Bind: CLICK
        $atag.bind('click', function (ev) {

          ev.stopPropagation();
          ev.preventDefault();

          var pk_category = $(this).data('pk');

          // Get all selected rows.
          var $tr_selected = $('tr.selected');
          if ($tr_selected.length < 1) {
            return false;
          }

          // Respect the lock state of the UI.
          if (that.ui_lock === true) {
            return false;
          }
          else {
            that._toggle_ui_lock();
          }

          // Quick prototype of a tiny poor man's queue counter.
          var $queue_count = {
            num_items: $tr_selected.length,
            decrease: function () {
              if (this.num_items == 1) {
                that._toggle_ui_lock();
              }
              else {
                this.num_items -= 1;
              }
            }
          };

          // Start ajax actions for each selected item.
          $.each($tr_selected, function (key, val) {
            var $pk_item = $(val).find('input.action-select');
            var pk_file = $(val).find('.fs_filepk').attr('data-filepk');
            that._GET_categories_by_file(pk_file, $pk_item);
            $pk_item.unbind().bind(
              'categories_lookup_ready',
              function (ev, pk_file, categories) {
                try {
                  that._PATCH_category_by_file(pk_file, pk_category, categories);
                  $pk_item.unbind().bind('PUT_category_by_file_complete', function () {
                    $queue_count.decrease();
                  })
                }
                catch (err) {
                  $queue_count.decrease();
                }
              });
          });
        });

        $li.append($atag);
        $buttons.push($li);
      });
      return $('<ul class="fs-categorizr-buttons" style="display: inline-block">').append($buttons);
    },

    /**
     * GET currently assigned categories for a file with PK pk_item. Optionally
     * pass a jQuery object to the second argument ``$fire_on`` to specify this
     * object as trigger-target for the ``categories_lookup_ready`` event.
     *
     * @param pk_file
     * @param $fire_on
     * @constructor
     */
    _GET_categories_by_file: function (pk_file, $fire_on) {

      if ($fire_on == undefined) {
        $fire_on = this.$api;
      }

      var csrftoken = getCookie('csrftoken');
      $.ajax({
        type: 'GET',
        url: '/api/v1/fsfilemodelext/' + pk_file + '/',
        context: this,
        contentType: 'application/json; charset=utf-8',
        beforeSend: function (xhr, settings) {
          xhr.setRequestHeader("X-CSRFToken", csrftoken);
        },
        success: function (data) {
          $fire_on.trigger(
            'categories_lookup_ready', [pk_file, data.category]);
        }
      });
    },

    /**
     * PATCH request to assign an item to files.
     *
     * @param pk_file
     * @param pk_category
     * @param extra_categories
     */

    // Dev-Note
    // --------
    // This method is biased because details make it rather useless for
    // DRY. Needs refactoring and further splitting up.
    // TODO  Refactor to be general purpose. Split assuming parts apart.

    _PATCH_category_by_file: function (pk_file, pk_category, extra_categories) {

      var csrftoken = getCookie('csrftoken');

      if (extra_categories == undefined) {
        extra_categories = [];
      }

      var new_category = "/api/v1/fscategories/" + pk_category + "/";

      // We need to check for dupes manually, since querying the rest interface
      // with two times the same list element results in a unique error on the DB
      var re = new RegExp(new_category, 'g');
      if (extra_categories.join('|').match(re) != undefined) {
        throw 'FS_DuplicateError';
      }

      if (pk_category > -1) {
        extra_categories.push(new_category);
      }

      $.ajax({
        type: 'PATCH',
        url: '/api/v1/fsfilemodelext/' + pk_file + '/',
        context: this,
        contentType: 'application/json; charset=utf-8',
        dataType: 'json',
        data: JSON.stringify({
          "filer_file": '/api/v1/fsfile/' + pk_file + '/',
          "category": extra_categories
        }),
        beforeSend: function (xhr, settings) {
          xhr.setRequestHeader("X-CSRFToken", csrftoken);
        },
        //                                                                     ___
        //                                                                 Success
        success: function (data) {
          // TODO  Untie this method from the change list page. Sep logic needed
          var $pk_item = $('a').find("[data-filepk='" + pk_file + "']")
            .parents('tr')
            .find('.action-checkbox input');
          $pk_item.trigger('PUT_category_by_file_complete');

          var $cat_col = $pk_item.closest('tr')
            .find('td:nth-child(' + this.cat_col_num + ')');

          var label = undefined;
          if (pk_category > -1) {
            label = 'Assigned category on ' + pk_file;
          }
          else {
            label = 'Removed category on ' + pk_file;
          }

          uib_notice.add_note(label, 2, 'check-circle');

          var categories = [];
          var ajax_requests = [];
          $.each(data.category, function (key, val) {
            ajax_requests.push(
              $.get(val, function (cdata) {
                categories.push(cdata);
              })
            );
          });

          $.when.apply($, ajax_requests).then(function () {

            var $categories = [];
            $.each(categories, function (key, val) {
              var $span = $('<span class="label cat">' + val.name + '</span>');
              var $atag = $('<a class="cat-del" ' +
                'data-catpk="' + val.id + '"' +
                'data-filepk="' + pk_file + '">x</a>');
              $span.append($atag);
              fs_categorizr.bind_quick_delete($span);

              $categories.push($span);

            });

            $cat_col.text('');
            $.each($categories, function (key, val) {
              $cat_col.append(val);
            });
          });
        }
      });
    },

    /**
     * Return categories. If ``force_fetch`` flag is true re-fetches from ajax.
     *
     * @param force_fetch
     * @returns {*}
     */
    get_categories: function (force_fetch) {

      if (force_fetch == undefined) {
        force_fetch = false;
      }

      if (this.categories == undefined || force_fetch === true) {
        this._fetch_categories()
      }

      return this.categories
    },

    /**
     * This method binds click events to the quick delete elements passed in.
     *
     * @param $el
     */
    bind_quick_delete: function ($el) {
      $el.find('a').bind('click', function (ev) {

        ev.preventDefault();
        ev.stopPropagation();

        var $this = $(this);
        var pk_file = $this.data('filepk');
        var pk_cat = $this.data('catpk');

        fs_categorizr.remove_category(pk_file, pk_cat);

      });
    },

    /**
     * Removes category from item via ajax.
     *
     * @param pk_file
     * @param pk_cat
     */
    remove_category: function (pk_file, pk_cat) {
      var that = this;
      $(this).one('categories_lookup_ready',
        function (ev, pk_file, categories) {

          var rem = '/api/v1/fscategories/' + pk_cat + '/';
          var re = new RegExp(rem, "g");

          $.each(categories, function (key, val) {
            if (val.match(re)) {
              categories.splice(key, 1);
              return false;
            }
          });

          that._PATCH_category_by_file(pk_file, -1, categories);
        });

      this._GET_categories_by_file(pk_file, $(this));
    },

    /**
     * Fetches categories by ajax
     *
     * @returns {*}
     * @private
     */
    _fetch_categories: function () {
      var url = '/api/v1/fscategories/';
      if (typeof(this.base_category) !== 'undefined') {
        url += '?slug_starts_with=' + this.base_category;
      }

      $.ajax({
        url: url,
        context: this,
        success: function (data) {
          this.categories = data;
          this.$api.trigger('categories_ready');
        }
      });
    },

    /**
     * Toggle ``ui_lock`` state for Categorizr.
     *
     * @private
     */
    _toggle_ui_lock: function () {
      this.ui_lock = !this.ui_lock;
      $('.fs_category_item a').toggleClass('ui-lock');
    }
  };


  /**
   * Timelinr
   * --------
   * Provides an ajax'ified way to add or remove all currently selected items
   * from the timeline display.
   */
  var fs_timelinr = {

    label: 'Tools to assign/remove selected items to/from the timeline.',
    icon: 'fa-clock-o',
    icon_type: 'fontawesome',
    band_bgcolor: 'inherit',    // inherit or color value
    band_colormode: 'normal',   // normal or inverted

    ui_lock: false,

    $timelinr: undefined,


    /**
     * Return timelinr or create it if it does not exist.
     *
     * @returns {*}
     */
    get_or_create: function () {

      if (this.$timelinr == undefined) {

        var that = this;

        $ul = $('<ul class=""></ul>');
        $li = $('<li class="fs-inline-help">' +
          '<i class="fa fa-question-circle" title="Select items in the list ' +
          'and click on “Add to timeline“ or “Remove from timeline“"></i>' +
          '</li><li class="fs-feature-title">On timeline?</li>');
        $ul.append($li);


        //                                                           _____________
        //                                                           Build Buttons
        $li_add = $('<li></li>');
        $atag_add = $('<a href="#" class="fs-timelinr-action" ' +
          'data-trigger="add"><b>Add</b> to timeline</a>');
        $li_rem = $('<li></li>');
        $atag_rem = $('<a href="#" class="fs-timelinr-action" ' +
          'data-trigger="remove"><b>Remove</b> from timeline</a>');

        $li_add.append($atag_add);
        $li_rem.append($atag_rem);

        //                                                                     ___
        //                                                             Bind: CLICK
        $atag_add.add($atag_rem).bind('click', function (ev) {

          ev.stopPropagation();
          ev.preventDefault();

          // TODO  Refactor to method, since we use it in various widgets
          var $tr_selected = $('tr.selected');
          if ($tr_selected.length < 1) {
            return false;
          }

          // Respect ui_lock and toggle it if UI is not locked.
          if (that.ui_lock === true) {
            return false;
          }
          else {
            that._toggle_ui_lock();
          }

          // Check if we want to add or remove the selected items.
          var is_timeline = undefined;
          var action = $(this).data('trigger');
          if (action == 'add') {
            is_timeline = true;
          }
          else if (action == 'remove') {
            is_timeline = false;
          }
          else {
            throw "Illegal action";
          }

          // TODO  Refactor to reusable class
          // Quick prototype of a tiny poor man's queue counter.
          var $queue_count = {
            num_items: $tr_selected.length,
            decrease: function () {
              if (this.num_items == 1) {
                that._toggle_ui_lock();
              }
              else {
                this.num_items -= 1;
              }
            }
          };

          $.each($tr_selected, function (key, val) {
            this.$pk_item = $(val).find('input.action-select');
            this.pk = this.$pk_item.val();
            var filepk = $(val).find('.fs_filepk').attr('data-filepk');
            var csrftoken = getCookie('csrftoken');

            $.ajax({
              type: 'PATCH',
              url: '/api/v1/fsfilemodelext/' + filepk + '/',
              context: this,
              contentType: 'application/json; charset=utf-8',
              dataType: 'json',
              data: JSON.stringify({
                'filer_file': '/api/v1/fsfile/' + filepk + '/',
                'is_timeline': is_timeline.toString()
              }),
              beforeSend: function (xhr, settings) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
              },
              //                                                           _______
              //                                                           Success
              success: function (data) {
                // Tell the counter it's one less to go.
                $queue_count.decrease();

                // Update UI: 1) Toggle symbol in list. 2) Add notification.
                var $ind = $(this.$pk_item.parents('tr').find('.fs_is-timeline-indicator')[0]);
                var label = undefined;
                if (is_timeline === true) {
                  label = 'File added to timeline';
                  $ind.removeClass('fa-times-circle').addClass('fa-check-circle');
                } else {
                  label = 'File removed from timeline';
                  $ind.removeClass('fa-check-circle').addClass('fa-times-circle');
                }
                // Push note to the notifier widget
                uib_notice.add_note(label, 2, 'check-circle');
              }
            });
          });

        });

        $ul.append($li_add).append($li_rem);

        this.$timelinr = $('<div class="fs_timelinr_container"></div>');
        this.$timelinr.append($ul);
        this.$timelinr.controller = this;
      }
      return this.$timelinr;

    },

    /**
     * Return timelinr or create it if it does not exist.
     *
     * @returns {*}
     */
    get_or_create: function () {

      if (this.$timelinr == undefined) {

        var that = this;

        $ul = $('<ul class=""></ul>');
        $li = $('<li class="fs-inline-help">' +
          '<i class="fa fa-question-circle" title="Select items in the list ' +
          'and click on “Add to timeline“ or “Remove from timeline“"></i>' +
          '</li><li class="fs-feature-title">On timeline?</li>');
        $ul.append($li);


        //                                                           _____________
        //                                                           Build Buttons
        $li_add = $('<li></li>');
        $atag_add = $('<a href="#" class="fs-timelinr-action" ' +
          'data-trigger="add"><b>Add</b> to timeline</a>');
        $li_rem = $('<li></li>');
        $atag_rem = $('<a href="#" class="fs-timelinr-action" ' +
          'data-trigger="remove"><b>Remove</b> from timeline</a>');

        $li_add.append($atag_add);
        $li_rem.append($atag_rem);

        //                                                                     ___
        //                                                             Bind: CLICK
        $atag_add.add($atag_rem).bind('click', function (ev) {

          ev.stopPropagation();
          ev.preventDefault();

          // TODO  Refactor to method, since we use it in various widgets
          var $tr_selected = $('tr.selected');
          if ($tr_selected.length < 1) {
            return false;
          }

          // Respect ui_lock and toggle it if UI is not locked.
          if (that.ui_lock === true) {
            return false;
          }
          else {
            that._toggle_ui_lock();
          }

          // Check if we want to add or remove the selected items.
          var is_timeline = undefined;
          var action = $(this).data('trigger');
          if (action == 'add') {
            is_timeline = true;
          }
          else if (action == 'remove') {
            is_timeline = false;
          }
          else {
            throw "Illegal action";
          }

          // TODO  Refactor to reusable class
          // Quick prototype of a tiny poor man's queue counter.
          var $queue_count = {
            num_items: $tr_selected.length,
            decrease: function () {
              if (this.num_items == 1) {
                that._toggle_ui_lock();
              }
              else {
                this.num_items -= 1;
              }
            }
          };

          $.each($tr_selected, function (key, val) {
            this.$pk_item = $(val).find('input.action-select');
            this.pk = this.$pk_item.val();
            var filepk = $(val).find('.fs_filepk').attr('data-filepk');
            var csrftoken = getCookie('csrftoken');

            $.ajax({
              type: 'PATCH',
              url: '/api/v1/fsfilemodelext/' + filepk + '/',
              context: this,
              contentType: 'application/json; charset=utf-8',
              dataType: 'json',
              data: JSON.stringify({
                'filer_file': '/api/v1/fsfile/' + filepk + '/',
                'is_timeline': is_timeline.toString()
              }),
              beforeSend: function (xhr, settings) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
              },
              //                                                           _______
              //                                                           Success
              success: function (data) {
                // Tell the counter it's one less to go.
                $queue_count.decrease();

                // Update UI: 1) Toggle symbol in list. 2) Add notification.
                var $ind = $(this.$pk_item.parents('tr').find('.fs_is-timeline-indicator')[0]);
                var label = undefined;
                if (is_timeline === true) {
                  label = 'File added to timeline';
                  $ind.removeClass('fa-times-circle').addClass('fa-check-circle');
                } else {
                  label = 'File removed from timeline';
                  $ind.removeClass('fa-check-circle').addClass('fa-times-circle');
                }
                // Push note to the notifier widget
                uib_notice.add_note(label, 2, 'check-circle');
              }
            });
          });

        });

        $ul.append($li_add).append($li_rem);

        this.$timelinr = $('<div class="fs_timelinr_container"></div>');
        this.$timelinr.append($ul);
        this.$timelinr.controller = this;
      }
      return this.$timelinr;

    },
    /**
     * Toggle ``ui_lock`` state for Widget.
     *
     * @private
     */
    _toggle_ui_lock: function () {
      this.ui_lock = !this.ui_lock;
      $('.fs_category_item a').toggleClass('ui-lock');
    }

  };


  /**
   * Notice
   * ------
   * This widget shows short notices like success or error badges. It complements
   * the default messaging system as it is only thought for short-lived notices
   * that indicate status after ajax'ified actions.
   */

  // Dev-Note
  // --------
  // When it turns out that this widget gets used a lot it might make sense to
  // turn it into an event-based process. Currently the display queue is
  // checked by a timer that runs periodically (1/s at the moment), which is
  // not the nicest design. But on the other hand, checking state once per
  // second does not put much stress on the CPU and seems well enough to make
  // this prototype run.

  var uib_notice = {
    $notice: undefined,
    standard: '',
    queue: {
      widget: undefined,
      is_busy: false,
      dismiss_at: undefined,
      note_loop: undefined,
      items: [],
      history: [],

      /**
       * Initialize the queing system.
       *
       * @param widget
       */
      init: function (widget) {
        this.widget = widget;
        var that = this;
        this.note_loop = setInterval(
          function () {
            that._check_messages(that)
          }, 1000);
      },

      /**
       * Checks the queue for messages to display.
       *
       * @param that
       * @private
       */
      _check_messages: function (that) {

        if (!that.is_busy && that.items.length > 0) {
          var current_item = that.items.splice(0, 1);
          that._display_message(current_item[0]);

        } else if (that.is_busy) {
          if (new Date().getTime() >= that.dismiss_at) {
            that.widget.$notice.fadeOut(188, function () {
              that.is_busy = false;
            })
          }
        }
      },

      /**
       * Displays one message in the Notice widget.
       *
       * @param item
       * @private
       */
      _display_message: function (item) {
        this.is_busy = true;
        this.dismiss_at = new Date(new Date().getTime() + 1000 * item.duration);
        this.widget.$notice.html(item.$note);
        this.widget.$notice.hide(0).fadeIn(188);
      }
    },

    /**
     * Initialize the Notice widget.
     */
    init: function () {
      this.queue.init(this);
    },

    /**
     * Returns the Notice widget and creates it if it does not already exist.
     *
     * @returns {*}
     */
    get_or_create: function () {
      if (this.$notice == undefined) {
        $el = $('<div class="uib-notice-container"></div>');
        $el.html('<span class="inactive"></span>');
        this.$notice = $el;
      }
      return this.$notice;
    },

    /**
     * Adds a note to the display queue.
     *
     * @param label
     * @param duration in seconds.
     * @param icon
     * @param msg
     */
    add_note: function (label, duration, icon, msg) {
      var $note = this._assemble_note(label, icon, msg);
      this.queue.items.push({'duration': duration, '$note': $note});
    },

    /**
     * Construct the HTML for a note object and return it to the caller.
     *
     * @param label
     * @param icon
     * @param msg
     * @returns {*|jQuery|HTMLElement}
     * @private
     */
    _assemble_note: function (label, icon, msg) {
      $note = $('<span class="uib-note"></span>');

      if (icon != undefined) {
        $icon = $('<i class="fa fa-' + icon + '"></i>');
      }
      else {
        $icon = $('<i class="fa fa-bullhorn"></i>');
      }

      $note.append($icon);

      $label = $('<span class="uib-label"> ' + label + '</span>');

      if (msg != undefined) {
        $label.attr('title', msg);
      }

      $note.append($label);
      return $note;
    }
  };

  /**
   * UI controller
   * -------------
   * This little piece just initializes our UI prototype
   */
  $(window).load(function () {
    //                                                    ________________________
    //                                                    Change list enhancements
    if ($('body').hasClass('change-list')) {

      $uib = fs_uiband.get_or_create();
      $('body').append($uib);

      $categorizr = fs_categorizr.get_or_create();
      fs_uiband.register_widget('categorizr', $categorizr);

      $timelinr = fs_timelinr.get_or_create();
      fs_uiband.register_widget('timelinr', $timelinr);

      //$setr = fs_setr.get_or_create();
      //fs_uiband.register_widget('setr', $setr);

      $notice = uib_notice.get_or_create();
      fs_uiband.$region_east.append($notice);

      fs_categorizr.bind_quick_delete($('span.label.cat'));

      uib_notice.init();
    }

    //                                                       _____________________
    //                                                       Set page enhancements
    if ($('body').hasClass('filersets-set') &&
      $('body').hasClass('change-form')) {
      sortr.init();
      set_type_cat_filter.init();
      set_type_field_config.init();
    }
  });

  /**
   * SetTypeCatFilter
   * ----------------
   * Reduces category tree to only show categories that belong to chosen
   * set type.
   */
  var set_type_cat_filter = {

    init: function () {
      if (typeof jss.filersets.setconfig.single_settype_pk == 'undefined') {
        var $set_type = $('select#id_settype');
        this._show_categories_for_value($set_type.val());
        $set_type.on('change', {that: this}, this.on_set_type_change);
      } else {
        this._show_categories_for_value(jss.filersets.setconfig.single_settype_pk);
      }
    },

    on_set_type_change: function (ev) {
      var that = ev.data.that;
      that._show_categories_for_value($(this).val());
    },

    _show_categories_for_value: function (settype_id) {
      var $set_type_categories = $('#id_category');
      $set_type_categories.find('li').css('display', 'none');
      $set_type_categories.find('li[data-settype-id="' + settype_id + '"]').css('display', 'block');
    }

  };

  /**
   * SetTypeFieldConfig
   * ------------------
   * Hides all input elements that according to the set type instance
   * configuration should not be visible for the selected set type.
   */
  // TODO(sthzg) Trigger events and let addon packages do their cleanup.
  var set_type_field_config = {

    init: function () {
      var $set_type = $('select#id_settype');
      this._show_inputs_for_set_type($set_type.val());
      $set_type.on('change', {that: this}, this.on_set_type_change);
    },

    on_set_type_change: function (ev) {
      var that = ev.data.that;
      that._show_inputs_for_set_type($(this).val());
    },

    _show_inputs_for_set_type: function (val) {
      var config = window.jss.filersets.setconfig['settype_' + val];
      // Iterates through all object properties and shows / hides
      // elements according to their boolean value.
      for (var property in config) {
        if (config.hasOwnProperty(property)) {
          if (!config[property]) {
            $('.' + property).parents('.form-row').css('display', 'none').addClass('hidden');
            // Hide django-suit tabs if necessary.
            $('.nav-tabs-suit a[href="#' + property + '"]').parents('li').css('display', 'none');
          } else {
            $('.' + property).parents('.form-row').css('display', 'block').removeClass('hidden');
            // Show django-suit tabs if necessary.
            $('.nav-tabs-suit a[href="#' + property + '"]').parents('li').css('display', 'inline-block');
          }
        }
      }

      // Check if fieldsets are empty/no more empty.
      // TODO(sthzg) Solution to support empty fieldsets in Suit tabs.
      if ($('#suit_form_tabs').length > 0) {
        return;
      }

      $.each($('fieldset'), function () {
        if ($(this).find('.form-row').not('.hidden').length < 1) {
          $(this).css('display', 'none');
        }
        else {
          $(this).css('display', 'block');
        }
      });
    }

  };

  /**
   * Sortr
   * -----
   * Allow users to sort sets by drag and drop.
   */
  var sortr = {

    $sortable: undefined,

    init: function () {

      var that = this;

      this.$sortable = $(".fs_list-sortable");

      this.$sortable.sortable({
        placeholder: "ui-state-highlight",
        sort: function (event, ui) {
        },
        start: function (event, ui) {
        },
        stop: function (event, ui) {
          that.update_sortr_values();
        },
        update: function (event, ui) {
          var $id_ordering = $('#id_ordering');
          $id_ordering.find('option[value="custom"]').prop('selected', true);
          $id_ordering.css('background-color', '#dff5e2');
        }
      });
      this.$sortable.sortable("option", "opacity", 0.8);
      this.$sortable.sortable("option", "revert", 150);
      this.$sortable.disableSelection();
    },

    update_sortr_values: function () {
      $('#id_item_sort_positions').val(
        this.$sortable.sortable('serialize', {attribute: 'data-itempk'})
      );
    }
  };

  // Get Cookie
  function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
      var cookies = document.cookie.split(';');
      for (var i = 0; i < cookies.length; i++) {
        var cookie = jQuery.trim(cookies[i]);
        // Does this cookie string begin with the name we want?
        if (cookie.substring(0, name.length + 1) == (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  // Locks process set button on click.
  $(document).ready(function () {
    $.each($('a[data-behavior="lock_on_click"]'), function (key, val) {
      var $that = $(this);
      $(this).on('click', function () {
        $that.off('click');
        $that.on('click', function (ev) {
          ev.preventDefault();
          ev.stopPropagation();
          return false;
        });

        $that.parents('li, td').css({
          'opacity': '.3'
        });
      });
    });
  });

}(django.jQuery || jQuery));