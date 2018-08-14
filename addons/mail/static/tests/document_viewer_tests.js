odoo.define('mail.document_viewer_tests', function (require) {
"use strict";

var DocumentViewer = require('mail.DocumentViewer');

var testUtils = require('web.test_utils');
var Widget = require('web.Widget');

QUnit.module('DocumentViewer', {

    beforeEach: function () {

        this.createViewer = function (parent, attachments, attachmentId) {
            var viewer = new DocumentViewer(parent, attachments, attachmentId);
            viewer.appendTo($("#qunit-fixture"));
            return viewer;
        },

        this.attachments = [
            {id: 1, datas_fname: 'filePdf.pdf', type: 'binary', mimetype: 'application/pdf', datas:'R0lGOP////ywAADs='},
            {id: 2, name: 'urlYoutubeName', type: 'url', mimetype: '', url: 'https://youtu.be/FYqW0Gdwbzk', datas_fname: 'urlYoutube'},
            {id: 3, name: 'urlGoogle', type: 'url', mimetype: '', url: 'https://www.google.com', datas_fname: 'urlRandom'},
            {id: 4, name: 'text.html', datas_fname: 'text.html', type: 'binary', mimetype: 'text/html', datas:'testee'},
            {id: 5, name: 'video.mp4', datas_fname: 'video.mp4', type: 'binary', mimetype: 'video/mp4', datas:'R0lDOP////ywAADs='},
            {id: 6, name: 'image.jpg', datas_fname: 'image.jpg', type: 'binary', mimetype: 'image/jpeg	', datas:'R0lVOP////ywAADs='},

        ];
    },
}, function () {

    QUnit.test('basic rendering', function (assert) {
        assert.expect(7);

        var viewer = this.createViewer(null, this.attachments, 1);
        testUtils.addMockEnvironment(viewer, {
            mockRPC: function (route, args) {
                if (route === '/web/static/lib/pdfjs/web/viewer.html?file=/web/content/1') {
                    return $.when();
                }
                return this._super.apply(this, arguments);
            },
        });

        assert.strictEqual(viewer.$('.o_viewer_content').length, 1,
            "there should be a preview");
        assert.strictEqual(viewer.$('.o_close_btn').length, 1,
            "there should be a close button");
        assert.strictEqual(viewer.$('.o_viewer-header').length, 1,
            "there should be a header");
        assert.strictEqual(viewer.$('.o_image_caption').length, 1,
            "there should be an image caption");
        assert.strictEqual(viewer.$('.o_viewer_zoomer').length, 1,
            "there should be a zoomer");
        assert.strictEqual(viewer.$('.fa-chevron-right').length, 1,
            "there should be a right nav icon");
        assert.strictEqual(viewer.$('.fa-chevron-left').length, 1,
            "there should be a left nav icon");

        viewer.destroy();
    });

    QUnit.test('Document Viewer PDF', function (assert) {
        assert.expect(4);

        var viewer = this.createViewer(null, this.attachments, 1);
        testUtils.addMockEnvironment(viewer, {
            mockRPC: function (route, args) {
                if (route === '/web/static/lib/pdfjs/web/viewer.html?file=/web/content/1') {
                    return $.when();
                }
                if (args.method === 'split_pdf') {
                    assert.deepEqual(args.args, [1, "", false], "should have the right arguments");
                    return $.when();
                }
                return this._super.apply(this, arguments);
            },
        });

        assert.strictEqual(viewer.$('.o_page_number_input').length, 1,
            "pdf should have a page input");
        assert.strictEqual(viewer.$('.o_remainder_input').length, 1,
            "pdf should have a remainder checkbox");
        assert.strictEqual(viewer.$('.o_split_btn').length, 1,
            "pdf should have a split button");

        viewer.$('.o_split_btn').click();

//        assert.strictEqual(viewer.$('.o_viewer_content').length, 0,
//            "there should not be a preview");
//        assert.strictEqual(viewer.$('.o_close_btn').length, 0,
//            "there should not be a close button");
//        assert.strictEqual(viewer.$('.o_viewer-header').length, 0,
//            "there should not be a header");
//        assert.strictEqual(viewer.$('.o_image_caption').length, 0,
//            "there should not be an image caption");
//        assert.strictEqual(viewer.$('.o_viewer_zoomer').length, 0,
//            "there should not be a zoomer");

        viewer.destroy();
    });

    QUnit.test('Document Viewer Youtube', function (assert) {
        assert.expect(2);

        var viewer = this.createViewer(null, this.attachments, 2);

        assert.strictEqual(viewer.$(".o_image_caption:contains('urlYoutubeName')").length, 1,
            "the viewer be on the right attachment");
        assert.strictEqual(viewer.$('.o_viewer_text[src="https://www.youtube.com/embed/FYqW0Gdwbzk"]').length, 1,
            "there should be a video player");

        viewer.destroy();
    });

    QUnit.test('Document Viewer html/(txt)', function (assert) {
        assert.expect(2);

        var viewer = this.createViewer(null, this.attachments, 4);

        assert.strictEqual(viewer.$(".o_image_caption:contains('text.html')").length, 1,
            "the viewer be on the right attachment");
        assert.strictEqual(viewer.$('iframe[src="/web/content/4"]').length, 1,
            "there should be an iframe with the right src");

        viewer.destroy();
    });

    QUnit.test('Document Viewer mp4', function (assert) {
        assert.expect(2);

        var viewer = this.createViewer(null, this.attachments, 5);

        assert.strictEqual(viewer.$(".o_image_caption:contains('video.mp4')").length, 1,
            "the viewer be on the right attachment");
        assert.strictEqual(viewer.$('.o_viewer_video').length, 1,
            "there should be a video player");

        viewer.destroy();
    });

    QUnit.test('Document Viewer jpg', function (assert) {
        assert.expect(2);

        var viewer = this.createViewer(null, this.attachments, 6);

       assert.strictEqual(viewer.$(".o_image_caption:contains('image.jpg')").length, 1,
            "the viewer be on the right attachment");
        assert.strictEqual(viewer.$('img[src="/web/image/6?unique=1"]').length, 1,
            "there should be a video player");

        viewer.destroy();
    });

});
});
