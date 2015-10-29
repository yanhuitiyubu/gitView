 (function($) {
 	var template1 = '\
        <ul>\
            <% _.each(context, function(parent, index) { %>\
            <li class="children">\
                <span><input type="checkbox" \
                <% var ps; %>\
                <% if ( !_.isUndefined(ps = _.find(options.selected, function(elem) { return elem.key === this.key; }, parent)) ) { %>\
                checked="checked"\
                <% } %> value="<%= parent.key %>" name="<%= checkboxname%>" id="<%= checkboxname%>"class="parent"/> <%= parent.text %></span>\
                <% if (options.startCollapsed) { %>\
                <ul style="display: none;">\
                <% } else { %>\
                <ul>\
                <% } %>\
                    <% _.each(parent.values, function(child, index) { %>\
                    <li>\
                        <span><input type="checkbox" \
                        <% if ( !_.isUndefined(this) && !_.isUndefined(_.find(this.values, function(elem) { return elem.key === this.key; }, child)) ) { %>\
                        checked="checked"\
                        <% } %> value="<%= child.key %>" name="sub<%= checkboxname%>" id="sub<%= checkboxname%>"/> <%= child.text %></span>\
                    </li>\
                    <% }, ps); %>\
                </ul>\
            </li>\
            <% }); %>\
        </ul>';
 
    var template2 = '\
        <ul>\
            <% _.each(context, function(parent, index) { %>\
            <li class="parent">\
                <span><input type="checkbox" \
                <% var ps; %>\
                <% if ( !_.isUndefined(ps = _.find(options.selected, function(elem) { return elem.key === this.key; }, parent)) ) { %>\
                checked="checked"\
                <% } %> value="<%= parent.key %>" name="<%= checkboxname%>" id="<%= checkboxname%>"class="parent"/> <%= parent.text %><i class="icon-chevron-up icon-black"></i></span>\
                <% if (options.startCollapsed) { %>\
                <ul style="display: none;">\
                <% } else { %>\
                <ul>\
                <% } %>\
                    <% _.each(parent.values, function(child, index) { %>\
                    <li>\
                        <span><input type="checkbox" \
                        <% if ( !_.isUndefined(this) && !_.isUndefined(_.find(this.values, function(elem) { return elem.key === this.key; }, child)) ) { %>\
                        checked="checked"\
                        <% } %> value="<%= child.key %>" name="sub<%= checkboxname%>" id="sub<%= checkboxname%>"/> <%= child.text %></span>\
                    </li>\
                    <% }, ps); %>\
                </ul>\
            </li>\
            <% }); %>\
        </ul>';
    
    /** Check all child checkboxes.
     * @param jQElement The parent <li>.
     */
    function _selectAllChildren(jQElement) {
        jQElement.find('ul > li > span > input[type="checkbox"]')
            .each(function() {
                $(this).prop('checked', true);
            });
    }
    
    /** Uncheck all child checkboxes.
     * @param jQElement The parent <li>.
     */
    function _deselectAllChildren(jQElement) {
        jQElement.find('ul > li > span > input[type="checkbox"]')
            .each(function() {
                $(this).prop('checked', false);
            });
    }
    
    /** Toggle all checkboxes.
     * @param[in] jQElement The root <ul> of the list.
     */
    function _toggleAllChildren(jQElement) {
        if (jQElement.children('span').children('input[type="checkbox"]').prop('checked')) {
            _selectAllChildren(jQElement);
        } else {
            _deselectAllChildren(jQElement);
        }
    }
    
    /** Toggle the collapse icon based on the current state.
     * @param[in] jQElement The <li> of the header to toggle.
     */
    function _toggleIcon(jQElement) {
        // Change the icon.
        if (jQElement.children('ul').is(':visible')) {
            // The user wants to collapse the child list.
            jQElement.children('span').children('i')
                .removeClass('icon-chevron-down')
                .addClass('icon-chevron-up');
        } else {
            // The user wants to expand the child list.
            jQElement.children('span').children('i')
                .removeClass('icon-chevron-up')
                .addClass('icon-chevron-down');
        }
    }
    
    /** Make sure there isn't any bogus default selections.
     * @param[in] selected The default selection object.
     * @return The filtered selection object.
     */
    function _validateDefaultSelectionValues(selected) {
        return _.filter(selected, function(elem) {
            return ( !_.isEmpty(elem.values) && !_.isUndefined(elem.values) );
        });
    }
    
    /** If a parent has at least one child node selected, check the parent.
     *  Conversely, if a parent has no child nodes selected, uncheck the parent.
     * @param[in] jQElement The parent <li>.
     */
    function _handleChildParentRelationship(jQElement) {
        // If the selected node is a child:
        if ( _.isEmpty(_.toArray(jQElement.children('ul'))) ) {
            var childrenStatuses = _.uniq(
                _.map(jQElement.parent().find('input[type="checkbox"]'), function(elem) {
                    return $(elem).prop('checked');
                })
            );
            
            // Check to see if any children are checked.
            if (_.indexOf(childrenStatuses, true) !== -1) {
                // Check the parent node.
                jQElement.parent().parent().children('span').children('input[type="checkbox"]').prop('checked', true);
            } else {
                // Uncheck the parent node.
                jQElement.parent().parent().children('span').children('input[type="checkbox"]').prop('checked', false);
            }
        }
    }
    
    /** Updates the internal object of selected nodes.
     */
    function _updateSelectedObject(jQElement) {
        var data = jQElement.data('listTree');

        // Filter the context to the selected parents.
        var selected = _.filter($.extend(true, {}, data.context), function(parent) {
            return jQElement.find('ul > li > span > input[value="' + parent.key + '"][name="' + jQElement.attr('id') + '"]').prop('checked');
        });
        
        // For each parent in the working context...
        _.each(selected, function(parent) {

            // Filter the children to the selected children.
            parent.values = _.filter(parent.values, function(child) {
                return jQElement.find('ul > li > span > input[value="' + child.key + '"][name="sub' + jQElement.attr('id') + '"]').prop('checked');
            });
        });

        // Update the plugin's selected object.
        data.options.selected = selected;
        jQElement.data('listTree', {
            "target": data.target,
            "context": data.context,
            "options": data.options,
        });
    }
    
    function _updateRelatedCheckboxList(masterEle, slaveEle, relationDict) {
    	var options = masterEle.data('listTree').options;
    	if (_.isEmpty(options.selected))
    	{
    		slaveEle.listTree('update', slaveEle.data('listTree').options.original);
    	}
    	else
    	{
    		var slaveIdArray = new Array();
    		var slaveFiltered = new Array();
    		var isSingleLevel = _.isUndefined(options.selected[0].values) || _.isEmpty(options.selected[0].values);
    		if (isSingleLevel)
    		{
    			_.each(options.selected, function(item){
    				Array.prototype.push.apply(slaveIdArray, relationDict[item.key]);
    			});
    		}
    		else
    		{
    			_.each(options.selected, function(item){
    				_.each(item.values, function(subitem){
    					Array.prototype.push.apply(slaveIdArray, relationDict[subitem.key]);
    				});
    			});
    		}
    		var uniqueIdArray = removeDuplicate(slaveIdArray);
    		if (_.isUndefined(slaveEle.data('listTree').options.original[0].values))
    		{
    			slaveFiltered = getSingleLevelItemsByIndex(uniqueIdArray, slaveEle.data('listTree').options.original);
    		}
    		else
    		{
    			slaveFiltered = getDoubleLevelItemsByIndex(uniqueIdArray, slaveEle.data('listTree').options.original);
    		}
    		slaveEle.listTree('update', slaveFiltered);
    	}
    }

    var methods = {
        init: function(context, options) {
            // Default options
            var defaults = {
                "startCollapsed": false,
                "original": context,
                "linkRelation": {},
                "linkObject": undefined
            };
            
            options = $.extend(defaults, options);
            
            // Validate the user entered default selections.
            // options.selected = _validateDefaultSelectionValues(options.selected);
            
            return this.each(function() {
                var $this = $(this),
                    data = $this.data('listTree');

                // If the plugin hasn't been initialized yet...
                if (!data) {

                    $(this).data('listTree', {
                        "target": $this,
                        "context": context,
                        "options": options,
                    });
                    
                    // Register checkbox handlers.
                    $(document).on('change', '#' + this.id + ' input[type="checkbox"]', function(e) {
                        var node = $(e.target).parent().parent();

                        // Toggle all children.
                        _toggleAllChildren(node);
                        
                        // Handle parent checkbox if all children are (un)checked.
                        _handleChildParentRelationship(node);
                        
                        // Filter context to selection and store in data.selected.
                        _updateSelectedObject($(this).parents('[class="listTree"]'));
                        
                        //Update the related checkbox list
                        var listTreeEle = $(this).parents('[class="listTree"]');
                        _updateRelatedCheckboxList(listTreeEle, listTreeEle.data('listTree').options.linkObject, listTreeEle.data('listTree').options.linkRelation);
                    })
                    
                    // Register collapse handlers on parents.
                    .on('click', '#' + this.id + ' > ul > li > span', function(e) {
                        var node = $(e.target).parent();
                        
                        // Change the icon.
                        _toggleIcon(node);
                        
                        // Toggle the child list.
                        node.children('ul').slideToggle('fast');
                        
                        e.stopImmediatePropagation();
                    });
                    
                    // Generate the list tree.
                    var template = template1;
                    if (context.length != 0 && context[0].values != undefined)
                    {
                    	template = template2
                    }
                    $this.html( _.template( template, { "context": context, "options": options, "checkboxname": this.id} ) );
                }
            });
        },
        destroy: function() {
            return this.each(function() {

                var $this = $(this),
                    data = $this.data('listTree');

                $(window).unbind('.listTree');
                $this.removeData('listTree');
            });
        },
        selectAll: function() {
            // For each listTree...
            return this.each(function() {
                // Select each parent checkbox.
                _selectAllChildren($(this));
                
                // For each listTree parent...
                $(this).find('ul > li:first-child').each(function() {
                    // Select each child checkbox.
                    _selectAllChildren($(this));
                });

                _updateSelectedObject($(this));
                
                _updateRelatedCheckboxList($(this), $(this).data('listTree').options.linkObject, $(this).data('listTree').options.linkRelation);
            });
        },
        deselectAll: function() {
            // For each listTree...
            return this.each(function() {
                // Deselect each parent checkbox.
                _deselectAllChildren($(this));
                
                // For each listTree parent...
                $(this).find('ul > li:first-child').each(function() {
                    // Deselect each child checkbox.
                    _deselectAllChildren($(this));
                });

                _updateSelectedObject($(this));
                
                _updateRelatedCheckboxList($(this), $(this).data('listTree').options.linkObject, $(this).data('listTree').options.linkRelation);
            });
        },
        expandAll: function() {
            // For each listTree...
            return this.each(function() {
                var node = $(this).children('ul').children('li');
                
                // Change the icon.
                _toggleIcon(node);
                
                // Show the child list.
                node.children('ul').slideDown('fast');
            });
        },
        collapseAll: function() {
            // For each listTree...
            return this.each(function() {
                var node = $(this).children('ul').children('li');
                
                // Change the icon.
                _toggleIcon(node);
                
                // Hide the child list.
                node.children('ul').slideUp('fast');
            });
        },
        update: function(context, newOptions) {
            // Default options
            var defaults = this.data('listTree').options;
            var	options;
            if (newOptions)
            {
            	options = $.extend(defaults, options);
            }
           	else
           	{
           		options = defaults;
           	}
            
            // Validate the user entered default selections.
            // options.selected = _validateDefaultSelectionValues(options.selected);
            
            return this.each(function() {
                var $this = $(this),
                    data = $this.data('listTree');

                // Ensure the plugin has been initialized...
                if (data) {
                    // Update the context.
                    $(this).data('listTree', {
                        "target": $this,
                        "context": context,
                        "options": options,
                    });
                    
                    // Generate the list tree.
                    var template = template1;
                    if (context.length != 0 && context[0].values != undefined)
                    {
                    	template = template2
                    }
                    $this.html( _.template( template, { "context": context, "options": options, "checkboxname": this.id} ) );
                }
            });
        }
    };

    $.fn.listTree = function(method) {

        if (methods[method]) {
            return methods[method].apply(this, Array.prototype.slice.call(arguments, 1));
        } else if (typeof method === 'object' || !method) {
            return methods.init.apply(this, arguments);
        } else {
            $.error('Method ' + method + ' does not exist on jQuery.listTree');
        }

    };
})(jQuery);
