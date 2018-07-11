odoo.define('project.PortalKanban', function (require) {
"use strict";

var AbstractController = require('web.AbstractController');
var KanbanColumn = require('web.KanbanColumn');
var KanbanModel = require('web.KanbanModel');
var KanbanView = require('web.KanbanView');
var PortalWebclientView = require('project.PortalWebclientView');
var rootWidget = require('root.widget');

var PortalKanban = PortalWebclientView.extend({
    template: 'project.portal_task_view_kanban',
    init: function (parent, params, options) {
        this.accessToken = params.accessToken;
        this.actionXmlId = 'project.action_portal_project_all_tasks';
        this.context = params.context;
        this.is_website = params.is_website;
        this.model = 'project.task';
        this.options = options;
        this.projectId = params.projectId;
        this.templateEdit = 'project.portaledit_view_task_kanban';
        this.viewType = 'kanban';
        this.viewName = 'project.task.kanban';

        this.domain = [['project_id', '=', this.projectId]];

        this._overrideAbstractController();
        this._overrideKanbanModel();

        this._super.apply(this, arguments);
    },
    /**
     * Callback function for _checkAccess.
     * This override is there to pass accessRights to _overrideKanbanColumn
     * after performing the default behaviour.
     *
     * @override
     * @param {string} accessRights: - 'edit' if access token and/or settings allow edit
     *                               - 'readonly' if access token and/or settings allow read only
     *                               - 'invalid' (default) if access token is invalid and user has no access
     */
    _checkAccessCallback: function (accessRights) {
        this._super.apply(this, arguments);
        this._overrideKanbanColumn(accessRights);
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
            readOnlyMode: true,
        };

        var view = new KanbanView(viewInfo, params);

        return view.getController(rootWidget);
    },
    /**
     * Performs various overrides on AbstractController.
     * - ensures that a task opens when clicking it
     * - ensures that the control elements are not rendered
     */
    _overrideAbstractController: function () {
        var self = this;
        AbstractController.include({
            /**
             * Opens a task on click
             * Note: doesn't open a project on click because clicking a
             *       project fires a 'button_clicked' event instead of an
             *       open_record' event (because the action type is 'object'
             *       and not 'open': see kanban_record.js > _onKanbanActionClicked)
             *
             * @override
             * @param {OdooEvent} event
             */
            _onOpenRecord: function (event) {
                var id = event.target.id || event.data.id ? this.model.get(event.data.id).data.id : undefined;
                self._redirect('/my/task/' + id);
            },
            /**
             * Prevent rendering of Control Panel elements
             *
             * @override
             */
            _renderControlPanelElements: function () {
            },
        });
    },
    /**
     * Performs various overrides on KanbanColumn:
     * - make use of a custom template
     * - make the records undraggable
     *
     * @param {string} accessRights: - 'edit' if access token and/or settings allow edit
     *                               - 'readonly' if access token and/or settings allow read only
     *                               - 'invalid' (default) if access token is invalid and user has no access
     */
    _overrideKanbanColumn: function (accessRights) {
        KanbanColumn.include({
            template: 'PortalKanbanView.Group',
            start: function () {
                this.draggable = accessRights === 'edit';
                // or this.$el.sortable("disable") after _super.apply to prevent moving within column
                this._super.apply(this, arguments);
            },
        });
    },
    /**
     * Intercepts the ID of the task being edited if there is one, so as to use it in _hijackRpcs
     */
    _overrideKanbanModel: function () {
        var self = this;
        KanbanModel.include({
            save: function (recordID, options) {
                var record = this.localData[recordID];
                self.currentlyEditedTask = record['model'] === 'project.task' ? record['res_id'] : false;
                return this._super.apply(this, arguments);
            },
        });
    },
});

return PortalKanban;
});
