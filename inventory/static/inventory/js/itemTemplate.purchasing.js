//
var app = app || {};

app.itmTmplt = Backbone.Model.extend({
    defaults: {
        barcode: null,
        description: null,
        brand: null,
        content: null,
        part_unit: null,
        yardage: null,
        notes: null,
        itmID: null,
        linked_code: null
    },
    idAttribute: 'barcode',
    urlRoot: '/inventory/api/item'
});

app.itemTemplateView = Backbone.View.extend({
    detailTemplate: null,
    editTemplate: null,
    events: {
        'click span.btn[title="Cancel"]': 'cancelChange',
        'click span.btn[title="CancelD"]': 'cancelChangeDetails',
        'keyup span.btn[title="Cancel"]': 'cancelKey',
        'keyup span.btn[title="CancelD"]': 'cancelKeyDetails',
        'click span.btn[title="Save"]': 'saveChange',
        'click span.btn[title="SaveD"]': 'saveChangeDetails',
        'keyup span.btn[title="Save"]': 'saveKey',
        'keyup span.btn[title="SaveD"]': 'saveKeyDetails'
    },
    validations: {
        description: { name: 'required', message: 'A description is required.' },
        linked_code: { name: 'required', args: ['false'] }
    },
    detailValidations: {
        units: [{ name: 'pattern', args: ['digits'], message: 'Whole numbers only' },
                   { name: 'range', args: [1, 999], message: 'Range is 1 through 999' }],
        eighths: [{ name: 'required' },
                     { name: 'pattern', args: ['digits'], message: 'Whole numbers only' },
                     { name: 'range', args: [0, 7], message: 'Range is 0 through 7' }],
        cost: { name: 'range', args: [0, 999999.99], message: 'Cost Range is 0.00 to 999999.99' },
        price: { name: 'range', args: [0, 999999.99], message: 'Price Range is 0.00 to 999999.99' }
    },
    initialize: function () {
        this.listenTo(app.invoice, 'change', this.eraseForm);
        this.listenTo(this.model, 'sync', this.renderItem);
        //
        _.bindAll(this, 'detailsResponse', 'fetchDetails', 'serverResponse');
    },
    cancelChange: function () {
        this.eraseForm();
    },
    cancelChangeDetails: function () {
        this.eraseForm();
    },
    cancelKey: function (e) {
        if (e.keyCode === 13) {
            this.cancelChange();
        }
    },
    cancelKeyDetails: function (e) {
        if (e.keyCode === 13) {
            this.cancelChangeDetails();
        }
    },
    checkDetails: function () {
        const parent = this.el;
        let data = parent.querySelectorAll('div.error');
        data.forEach(function (elem) {
            elem.innerHTML = '';
        });
        data = parent.querySelectorAll('input');
        let changes = Backbone.Validation.checkForm(this.detailValidations, data, this.model);
        //  show errors
        data.forEach(function (elem) {
            if (elem.hasAttribute('data-error')) {
                const lbl = 'div.error[data-name="' + elem.name + '"]';
                const dest = parent.querySelector(lbl);
                dest.innerHTML = elem.getAttribute('data-error');
                changes = null;
                }
        });
        return changes;
    },
    checkForm: function () {
        const ydg = this.el.querySelector('input[name="yardage"]');
        const tf = (ydg.checked) ? 'True' : 'False';
        ydg.setAttribute('value', tf);
        const data = this.el.querySelectorAll('input,textarea');
        let changes = Backbone.Validation.checkForm(this.validations, data, this.model);
        // show errors
        const src = this.el.querySelector('input.invalid');
        const dest = this.el.querySelector('div.error');
        const msg = src ? src.getAttribute('data-error') : '';
        dest.innerHTML = msg;
        if ( src !== null ) { changes = null; }
        return changes;
    },
    detailsResponse: function (m, r, o) {
        if (o.source === 'stock') {
            m.fetchCount = m.fetchCount + 1;
            this.model.set('units', ('errors' in r) ? null : r.units);
            this.model.set('eighths', ('errors' in r) ? null : r.eighths);
        }
        if (o.source === 'price') {
            m.fetchCount = m.fetchCount + 2;
            this.model.set('price', ('errors' in r) ? null : r.price);
        }
        if (o.source === 'purchase') {
            m.fetchCount = m.fetchCount + 3;
            // will not return errors
            let cost = null;
            if (r.count > 0) {
                cost = r.objects[r.count - 1].cost;
            }
            this.model.set('cost', cost);
        }
        //  after all three fetches have completed,
        //  call renderDetails
        if (m.fetchCount === 6) {
            m.fetchCount = 0;
            this.renderDetails();
            }
    },
    eraseForm: function () {
        this.$el.html(' ');
    },
    fetchDetails: function () {
        app.detailsRecord.fetchCount = 0;
        const bc = this.model.get('barcode');
        //  fetch units, eighths from StockBook
        const opts = {
            url: '/inventory/api/stock/' + bc,
            success: this.detailsResponse,
            error: this.detailsResponse,
            source: 'stock',
            wait: true
            };
        app.detailsRecord.fetch(opts);
        //  fetch price from Price
        opts.url = '/inventory/api/price/' + bc;
        opts.source = 'price';
        app.detailsRecord.fetch(opts);
        //  fetch cost from Purchase ( most recent invoice )
        opts.url = '/inventory/api/purchase?item=' + bc;
        opts.source = 'purchase';
        app.detailsRecord.fetch(opts);
    },
    renderDetails: function () {
        if (this.detailTemplate === null) {
            const ctxt = $('#editItemDetails').html();
            const tmplt = _.unescape(ctxt);
            this.detailTemplate = _.template(tmplt);
        }
        const tf = this.model.get('yardage')
        this.model.set('spanclass', (tf) ? '' : 'hidden');
        this.model.set('unit_label', (tf) ? 'Yards' : 'Count');
        const itmView = this.detailTemplate(this.model.attributes);
        this.$el.html(itmView);
    },
    renderItem: function (model, response, options) {
        if (this.editTemplate === null) {
            const ctxt = $('#editItemTemplate').html();
            const tmplt = _.unescape(ctxt);
            this.editTemplate = _.template(tmplt);
        }
        if ('saved' in options) return;
        //  if not found in database, assume lookup value was UPC
        if (!this.model.get('itmID')) {
            this.model.set(this.model.defaults);
            this.model.set('linked_code', this.model.get('digitstring'));
        }
        const itmView = this.editTemplate(this.model.attributes);
        this.$el.html(itmView);
        const inp = this.el.querySelector('input[name="yardage"]');
        const tf = this.model.get('yardage') === true;
        inp.setAttribute('checked', tf);
        inp.setAttribute('value', tf);
    },
    saveChange: function () {
        const changes = this.checkForm();
        if (changes === null) return; //  errors found
        const opts = {
                wait: true,
                saved: true,
                success: this.fetchDetails
                };
        this.model.save(changes, opts);
    },
    saveChangeDetails: function () {
        const changes = this.checkDetails();
        if (changes === null) return; //  errors found
        changes.item = this.model.get('barcode');
        changes.invoice = app.invoice.get('id');
        const opts = {
            wait: true,
            url: '/inventory/api/itemdata',
            success: this.serverResponse
        }
        app.detailsRecord.clear();
        app.detailsRecord.save(changes, opts);
        // store the data onto the server
    },
    saveKey: function (e) {
        if (e.keyCode === 13) {
            this.saveChange();
        }
    },
    saveKeyDetails: function (e) {
        if (e.keyCode === 13) {
            this.saveChangeDetails();
        }
    },
    serverResponse: function (m, r, o) {
    //  save updated values to dataItem
        for (const attr in m.attributes) {
            if (attr in this.model.attributes) {
                const val = m.attributes[attr];
                if (val !== this.model.get(attr)) {
                    this.model.set(attr, val);
                }
            }
        }
        app.detailsView.addToList(this.model);
        this.eraseForm();
    }
});
