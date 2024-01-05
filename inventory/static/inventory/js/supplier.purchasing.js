//
var app = app || {};

app.supplier = Backbone.Model.extend({
    defaults: {
        id: null,
        name: null,
        street: null,
        street_ext: null,
        city: null,
        state: null,
        zip5: null,
        phone_1: null,
        phone_2: null,
        notes: null
    },
    url: '/inventory/api/supplier',
    render: function () {
        const node = document.createElement('option');
        node.setAttribute('value', this.get('id'));
        node.setAttribute('label', this.get('name'));
        return node;
    }
});

app.supplierListView = Backbone.View.extend({
    editTemplate: null,
    model: new app.supplier(),
    events: {
        change: 'changeSupplier',
        'click span.btn[title="Cancel"]': 'cancelChange',
        'keyup span.btn[title="Cancel"]': 'cancelKey',
        'click span.btn[title="New"]': 'editSupplier',
        'keyup span.btn[title="New"]': 'editKey',
        'click span.btn[title="Save"]': 'saveChange',
        'keyup span.btn[title="Save"]': 'saveKey'
    },
    validations: {
        name: { name: 'required', message: 'A name is required.' },
        zip5: [
                   { name: 'required', args: [false] },
                   {
                     name: 'pattern',
                     args: [/^\d{5}$/],
                     message: 'Please enter a five-digit zipcode.'
                    }
              ],
        phone_1: [
                   { name: 'required', args: [false] },
                   {
                    name: 'pattern',
                    message: 'Enter a 7- or 10-digit number',
                    args: [/^(\(?(\d{3})\)?[- ]?)?(\d{3})[- ]?(\d{4})$/]
                    }
                 ],
        phone_2: [
                    { name: 'required', args: [false] },
                    {
                    name: 'pattern',
                    message: 'Enter a 7- or 10-digit number',
                    args: [/^(\(?(\d{3})\)?[- ]?)?(\d{3})[- ]?(\d{4})$/]
                    }
                 ]
    },
    initialize: function () {
        this.selector = this.el.querySelector('select#suppliers');
        this.formBox = this.el.querySelector('div#formBox');
        _.bindAll(this, 'createSupplierList', 'serverResponse');
        this.model.fetch({success: this.createSupplierList});
    },
    addSupplier: function () {
        // create 'option' element and add to select
        const last = this.selector.options.length;
        const option = this.model.render();
        this.selector.add(option);
        this.selector.selectedIndex = last;
        this.changeSupplier();
        this.formBox.innerHTML = '';
    },
    cancelChange: function () {
        this.formBox.innerHTML = '';
    },
    cancelKey: function (e) {
        if (e.keyCode === 13) {
            this.cancelChange();
        }
    },
    changeSupplier: function () {
        app.invoice.setVendor(this.selector.selectedIndex);
    },
    checkForm: function () {
        const data = this.el.querySelectorAll('input,textarea');
        const changes = Backbone.Validation.checkForm(this.validations, data, this.model);
        // display errors, if any
        let dest = this.el.querySelectorAll('div.error');
        dest.forEach(function (el) { el.innerHTML = ''; });
        data.forEach(function (el) {
            if (!el.classList.contains('invalid')) return;
            const msg = el.getAttribute('data-error');
            dest = el.parentElement.querySelector('div.error');
            dest.innerHTML = msg;
        });
        return changes;
    },
    createSupplierList: function(model, response, opts) {
        response.objects.forEach((mdl) => {
            Object.assign(this.model.attributes, mdl);
            this.selector.add(this.model.render());
            });
        return;
    },
    editKey: function (e) {
        if (e.keyCode === 13) {
            this.editSupplier();
        }
    },
    editSupplier: function () {
        this.model.set(this.model.defaults);
        this.renderEdit();
    },
    renderEdit: function () {
        if (this.editTemplate === null) {
            const ctxt = $('#editSupplier').html();
            const tmplt = _.unescape(ctxt);
            this.editTemplate = _.template(tmplt);
        }
        const supView = this.editTemplate(this.model.attributes);
        this.formBox.innerHTML = supView;
    },
    saveChange: function () {
        const changes = this.checkForm();
        if (!changes) return; //  errors found
        if (!Object.keys(changes).length) { //  no errors, but no changes
          this.cancelChange();
          return;
        }
        const opts = {
                    wait: true,
                    success: this.serverResponse
                    };
        this.model.save(changes, opts);
    },
    saveKey: function (e) {
        if (e.keyCode === 13) {
            this.saveChange();
        }
    },
    serverResponse: function (model, response) {
        if ('id' in response) {
            this.addSupplier();
            } else { // we have errors
            for (const fld in response.errors) {
                const msg = response.errors[fld];
                const selector = 'input[name="' + fld + '"]';
                const src = this.formBox.querySelector(selector);
                src.classList.add('invalid');
                src.setAttribute('data-error', msg);
                const dest = this.formBox.querySelector('div.error');
                dest.innerHTML = msg;
                }
            }
    }
});
