//
Backbone.View.prototype.close = function () {
  this.remove();
  this.unbind();
  if (this.onClose) {
    this.onClose();
  }
}
var app = app || {};

app.itmTmplt = Backbone.Model.extend({
    defaults: {
        description: null,
        barcode: null,
        brand: null,
        content: null,
        part_unit: null,
        yardage: null,
        notes: null,
        itmID: null,
        linked_code: null
    },
    idAttribute: 'barcode'
});

app.itmTmpltList = Backbone.Collection.extend({
    model: app.itmTmplt,
    url: '/inventory/api/item'
});

app.itmTmpltView = Backbone.View.extend({
    className: 'itemTemplate',
    editTemplate: null,
    showTemplate: null,
    events: {
        'click span.btn[title="Cancel"]': 'cancelChange',
        'keyup span.btn[title="Cancel"]': 'cancelKey',
        'click span.btn[title="Edit"]': 'editItemTemplate',
        'keyup span.btn[title="Edit"]': 'editKey',
        'click span.btn[title="Print"]': 'printItemTemplate',
        'keyup span.btn[title="Print"]': 'printKey',
        'click span.btn[title="Save"]': 'saveChange',
        'keyup span.btn[title="Save"]': 'saveKey'
    },
    validations: {
        description: { name: 'required', message: 'A description is required.' }
    },
    initialize: function () {
        this.listenTo(this.model, 'change', this.render);
    },
    cancelChange: function () {
        const bc = this.model.get('barcode');
        if (bc) { // was editing a known itemTemplate
            this.render();
        } else { // was adding a new itemTemplate
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
        // show errors
        const src = this.el.querySelector('input.invalid');
        const dest = this.el.querySelector('div.error');
        const msg = src ? src.getAttribute('data-error') : '';
        dest.innerHTML = msg;
        //  extra tests
        if (changes) {
            const ydg = this.el.querySelector('#ydg').checked ? 'True' : 'False';
            if (this.model.get('yardage') !== ydg) {
                changes.yardage = ydg;
            }
        }
        return changes;
    },
    editItemTemplate: function () {
        const editing = this.el.parentElement.querySelector('span.btn[title="Save"]');
        if (editing) return;

        const lv = this.renderEdit();
        const fld = lv.el.querySelector("input[name='description']");
        fld.focus();
    },
    editKey: function (e) {
        if (e.keyCode === 13) {
            this.editItemTemplate();
        }
    },
    printItemTemplate: function () {
        this.model.save(null, { patch: true, wait: true });
    },
    printKey: function (e) {
        if (e.keyCode === 13) {
            this.printItemTemplate();
        }
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
        if ('locID' in response) { //  success
            const isNew = (model._previousAttributes.locID === null);
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
        if (this.showTemplate === null) {
            const ctxt = $('#showBox').html();
            const tmplt = _.unescape(ctxt);
            this.showTemplate = _.template(tmplt);
        }
        const itmView = this.showTemplate(this.model.attributes);
        this.$el.html(itmView);
      return this;
    },
    renderEdit: function () {
        if (this.editTemplate === null) {
            const ctxt = $('#editBox').html();
            const tmplt = _.unescape(ctxt);
            this.editTemplate = _.template(tmplt);
        }
        const ydg = this.model.get('yardage');
        const itmView = this.editTemplate(this.model.attributes);
        this.$el.html(itmView);
        if (ydg === 'True') {
            const inp = this.el.querySelector('#ydg');
            inp.setAttribute('checked', 'checked');
        }
      return this;
    }
});
//
app.itmTmpltListView = Backbone.View.extend({
    el: '#wrapper',
    events: {
        'click #wrapper button[title="Add"]': 'addItemTemplate'
    },
    initialize: function (items) {
        this.body = this.el.querySelector('div.bodyspace');
        this.collection = new app.itmTmpltList(items);
        this.render();
    },
    addItemTemplate: function () {
        const editing = this.body.querySelector('span.btn[title="Save"]');
        if (editing) return;
//
        let fld = this.body.querySelector('div.noContent');
        if (fld) {
            this.body.removeChild(fld);
        }
        const item = new app.itmTmplt();
        item.urlRoot = app.itmTmpltList.prototype.url;
        item.grouping = this.collection;
        const tmpltView = new app.itmTmpltView({
            model: item,
            collection: this.collection
        });
        const lv = tmpltView.renderEdit();
        fld = lv.el.querySelector("input[name='description']");
        this.body.appendChild(lv.el);
        fld.focus();
    },
    render: function () {
        if (this.collection.length) {
            while (this.body.children.length) {
                this.body.removeChild(this.body.children[0]);
            }
            this.collection.each(function (item) {
                this.renderItemTemplate(item);
            }, this);
        } else {
            const nC = document.createElement('div');
            nC.setAttribute('class', 'noContent');
            nC.appendChild(document.createTextNode('No items found'));
            this.body.appendChild(nC);
        }
    },
    renderItemTemplate: function (item) {
        const tmpltView = new app.itmTmpltView({
            model: item
        });
       const lv = tmpltView.render();
        this.body.appendChild(lv.el);
    }
});
//
