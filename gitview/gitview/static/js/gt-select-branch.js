var gitview = window.gitview || {};

gitview.branchReport = {
  init: function() {
    this.fillBranches();
    this.initSelectProjectEvent();
  },

  fillBranches: function() {
    var projectOptions = $('select.js-project');
    var selectedProjects = $(projectOptions).find('option[selected=selected]');
    // when page show search result,
    // the project and branch shows as previous selected one,
    // so skip to fill branch list.
    if (selectedProjects.length == 0) {
      var projectId = $('select.js-project option').first().attr('value');
      this.loadBranches(projectId);
    }
  },

  loadBranches: function(selectedProjectId) {
    var url = '/projects/' + selectedProjectId + '/branches/';
    $.ajax({
      url: url,
      type: 'GET',
      dataType: 'json',
      success: function(data, status, xhr) {
        var branchSelect = $('select.js-branch');
        var branches = data;
        // remove all previous branch list
        branchSelect.children().remove();
        // add default option
        branches.forEach(function(branch) {
          branchOption = new Option(branch.name, branch.pk);
          branchSelect.append(branchOption);
        });
      },
      error: function() {
        alert('failed to get branch list for project:' + this.id);
      }
    });
  },

  initSelectProjectEvent: function() {
    var that = this;
    $('select.js-project').on('change', function(e) {
      selectedProjectId = this.value;
      $(this).find('option[selected=selected]').removeAttr('selected');
      $(this).find("option[value=" + this.value + "]").attr('selected', true);
      var branchSelect = $('select.js-branch');
      var defaultOption = branchSelect.find('.js-default-option');
      if (selectedProjectId !== '') {
        that.loadBranches(selectedProjectId);
      }
      else {
        branchSelect.children().remove();
      };
    });
  },
};


$(document).ready(function(){
  gitview.branchReport.init();
});
