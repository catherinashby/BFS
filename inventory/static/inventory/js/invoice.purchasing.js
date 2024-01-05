//
var app = app || {};

app.invoiceModel = Backbone.Model.extend({
    setVendor: function (nmbr) {
        if (nmbr > 0) {
            const attrs = { id: null, vendor_id: nmbr };
            const options = {
                url: '/inventory/api/invoice',
                wait: true
            };
            this.save(attrs, options);
        } else {
            this.clear();
        }
    }
});

app.invoiceView = Backbone.View.extend({
    initialize: function () {
        this.listenTo(this.model, 'change', this.showInvoice);
    },
    showInvoice: function (model, response, options) {
        if (response.errors) {
            this.render(response.errors.vendor_id);
        } else {
            this.render();
        }
    },
    render: function (txt) {
        if (txt == null) {
            const n = this.model.get('id');
            txt = n ? 'Invoice #' + n : '';
            }
        this.el.textContent = txt;
    }
});

app.inputView = Backbone.View.extend({
    events: {
        'change input[name="digitString"]': 'parseEntry'
    },
    initialize: function () {
        this.inp = this.el.querySelector('input[name="digitString"]');
        this.divErr = this.el.querySelector('div.error');
        this.listenTo(app.invoice, 'change', this.renderItemArea);
    },
    parseEntry: function () {
        this.divErr.innerHTML = '';
        const ds = this.inp.value || '';
        if (!/^\d+$/.test(ds)) {
            this.showError('Please enter only digits');
            return;
        }
        const options = {
            url: '/inventory/api/itemdata/' + ds,
            wait: true
            };
        app.dataItem.clear();
        app.dataItem.fetch(options);
        this.inp.value = '';
        },
    renderItemArea: function () {
        this.inp.value = '';
        const invID = app.invoice.get('id');
        if (invID) { // display the input field
            this.el.classList.remove('hidden');
        } else { // hide the input field
            this.el.classList.add('hidden');
        }
    },
    showError: function (msg) {
        this.divErr.innerHTML = msg;
    }
});
