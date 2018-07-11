odoo.define('project.PortalForm', function (require) {
"use strict";

var FormView = require('web.FormView');
var PortalWebclientView = require('project.PortalWebclientView');
var RelationalFields = require('web.relational_fields');
var rootWidget = require('root.widget');

var FieldMany2One = RelationalFields.FieldMany2One;

var PortalForm = PortalWebclientView.extend({
    template: 'project.portal_task_view_form',
    init: function (parent, params, options) {
        var self = this;

        this.accessToken = params.accessToken;
        this.context = params.context;
        this.is_website = params.is_website;
        this.model = 'project.task';
        this.options = options;
        this.options['search'] = false; // cannot search on a form
        this.projectId = params.projectId;
        this.taskId = params.taskId;
        this.templateEdit = 'project.portaledit_view_task_form';
        this.viewType = 'form';
        this.viewName = 'project.task.form';

        this.domain = [['id', '=', this.taskId]];

        this._overrideFieldMany2One();

        this._super.apply(this, arguments);
    },
    /**
     * Create a controller for a given view, and make sure that
     * data and libraries are loaded.
     *
     * @param {Object} viewInfo the result of a fields_view_get() method of a model
     * @param {string[]} domain (optional)
     * @returns {Deferred} The deferred resolves to a controller
     */
    _getController: function (viewInfo, domain) {
        domain = domain || this.domain;
        var params = {
            modelName: this.model,
            domain: domain,
            context: this.context,
            currentId: this.taskId,
            readOnlyMode: true,
        };

        return new FormView(viewInfo, params)
            .getController(rootWidget);
    },
    /**
     * Performs various overrides on FieldMany2One in order for the link to the project on
     * the form view to redirect to the portal kanban view of the project
     */
    _overrideFieldMany2One: function () {
        FieldMany2One.include({
            /**
             * Add a portal link if the field links to project.project.
             * Otherwise, add the default link.
             *
             * @override
             */
            _renderReadonly: function () {
                this._super.apply(this, arguments);
                if (this.field.relation === 'project.project' && !this.nodeOptions.no_open && this.value) {
                    this.$el.attr('href', _.str.sprintf('/my/project/%s%s', this.value.res_id, window.top.location.search));
                };
            },

            /**
             * Prevent the onclick event from bubbling up
             * if the field links to project.project
             *
             * @override
             * @param {MouseEvent} event
             */
            _onClick: function (event) {
                if (this.field.relation !== 'project.project') {
                    this._super.apply(this, arguments);
                };
            },
        });
    },
});

return PortalForm;
});
