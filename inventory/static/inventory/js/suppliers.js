//
Backbone.View.prototype.close = function () {
  this.remove();
  this.unbind();
  if (this.onClose) {
    this.onClose();
  }
}
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
    }
});

app.supplierList = Backbone.Collection.extend({
    model: app.supplier,
    url: '/inventory/api/supplier'
});

app.supplierView = Backbone.View.extend({
    className: 'supplier',
    editTemplate: null,
    showTemplate: null,
    events: {
        'click span.btn[title="Cancel"]': 'cancelChange',
        'keyup span.btn[title="Cancel"]': 'cancelKey',
        'click span.btn[title="Edit"]': 'editSupplier',
        'keyup span.btn[title="Edit"]': 'editKey',
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
        this.listenTo(this.model, 'change', this.render);
    },
    cancelChange: function () {
        const num = this.model.get('id');
        if (num) { // was editing a known supplier
            this.render();
        } else { // was adding a new supplier
            this.close();
        }
    },
    cancelKey: function (e) {
        if (e.keyCode === 13) {
            this.cancelChange();
        }
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
    editKey: function (e) {
        if (e.keyCode === 13) {
            this.editSupplier();
        }
    },
    editSupplier: function () {
        const editing = this.el.parentElement.querySelector('span.btn[title="Save"]');
        if (editing) return;

        const lv = this.renderEdit();
        const fld = lv.el.querySelector("input[name='name']");
        fld.focus();
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
                     view: this,
                     template: this.editTemplate,
                     success: this.serverResponse
                     };
        this.model.save(changes, opts);
    },
    saveKey: function (e) {
        if (e.keyCode === 13) {
            this.saveChange();
        }
    },
    serverResponse: function (model, response, options) {
        if ('id' in response) { //  success
            const isNew = (model._previousAttributes.id == null);
            if (isNew) {
                model.grouping.add(model);
            }
        } else {
            //  we have errors; re-display the form
            options.view.$el.html(options.template(model.attributes));
            const box = options.view.el;
            const errs = response.errors;
//
            for (const fld in errs) {
                const msg = errs[fld];
                const selector = 'input[name="' + fld + '"]';
                const src = box.querySelector(selector);
                src.classList.add('invalid');
                src.setAttribute('data-error', msg);
                const dest = box.querySelector('div.error');
                dest.innerHTML = msg;
                //  reset the model to last correct value
                model.attributes[fld] = model._previousAttributes[fld];
            }
        }
    },
    render: function () {
        if (this.showTemplate == null) {
            const ctxt = $('#showBox').html();
            const tmplt = _.unescape(ctxt);
            this.showTemplate = _.template(tmplt);
        }
        const supView = this.showTemplate(this.model.attributes);
        this.$el.html(supView);
      return this;
    },
    renderEdit: function () {
        if (this.editTemplate == null) {
            const ctxt = $('#editBox').html();
            const tmplt = _.unescape(ctxt);
            this.editTemplate = _.template(tmplt);
        }
        const supView = this.editTemplate(this.model.attributes);
        this.$el.html(supView);
      return this;
    }
});

app.supplierListView = Backbone.View.extend({
    el: '#wrapper',
    events: {
        'click #wrapper button[title="Add"]': 'addSupplier'
    },
    initialize: function (sups) {
        this.body = this.el.querySelector('div.bodyspace');
        this.collection = new app.supplierList(sups);
        this.render();
    },
    addSupplier: function () {
        const editing = this.body.querySelector('span.btn[title="Save"]');
        if (editing) return;
//
        let fld = this.body.querySelector('div.noContent');
        if (fld) {
            this.body.removeChild(fld);
        }
        const item = new app.supplier();
        item.urlRoot = app.supplierList.prototype.url;
        item.grouping = this.collection;
        const supView = new app.supplierView({
            model: item,
            collection: this.collection
        });
        const lv = supView.renderEdit();
        fld = lv.el.querySelector('input[name="name"]');
        this.body.appendChild(lv.el);
        fld.focus();
    },
    render: function () {
        if (this.collection.length) {
            while (this.body.children.length) {
                this.body.removeChild(this.body.children[0]);
            }
            this.collection.each(function (item) {
                this.renderSupplier(item);
            }, this);
        } else {
            const nC = document.createElement('div');
            nC.setAttribute('class', 'noContent');
            nC.appendChild(document.createTextNode('No suppliers found'));
            this.body.appendChild(nC);
        }
    },
    renderSupplier: function (item) {
        const supView = new app.supplierView({
            model: item
        });
        const lv = supView.render();
        this.body.appendChild(lv.el);
    }
});
