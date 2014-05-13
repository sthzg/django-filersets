$('document').ready(function() {
  $('#result_list tbody tr').bind(
      'click',
      function() {
        var $cb = $(this).find('.action-checkbox input');
        $cb.prop('checked', !$cb.prop("checked"));
        $(this).toggleClass('selected');
  });
});