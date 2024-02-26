//
Backbone.View.prototype.close = function () {
  this.remove();
  this.unbind();
  if (this.onClose) {
    this.onClose();
    }
  }

var app = app || {};

app.templates = {};

app.stockItem = Backbone.Model.extend({
  defaults: {
    itm: null,
    itm_type: null,
    loc: null,
    units: null,
    created: null,
    updated: null
  },
  idAttribute: 'itm'
});

app.stockList = Backbone.Collection.extend({
  model: app.stockItem,
  url: '/inventory/api/stock',
  parse: function (r) {
    for (const itm of r.objects) {
      if (itm.itm_type == 0) {
        itm.units = Math.floor(itm.units);
      }
    }
    return r.objects;
  }
});

app.stockItemView = Backbone.View.extend({
  className: "stockItem group",
  events: {
    'click span.btn[title="Cancel"]': 'cancelItem',
    'keyup span.btn[title="Cancel"]': 'cancelKey',
    'click span.btn[title="Edit"]': 'editItem',
    'keyup span.btn[title="Edit"]': 'editKey',
    'click span.btn[title="Save"]': 'saveItem',
    'keyup span.btn[title="Save"]': 'saveKey',
  },
  validations: {
      units_decimal: {
               name: 'pattern',
               message: 'Enter a number',
               args: [/^(?:\d{1,3})(?:\.\d{0,3})?$/]
                 },
      units_integer: {
               name: 'pattern',
               message: 'Enter a number',
               args: [/^(?:\d{1,3})$/]
                 }
  },
  initialize: function () {
    this.render();
    this.setFields();
    return;
  },
  render: function () {
    const display = app.templates['stockTemplate'].innerHTML;
    const formatter = _.template(_.unescape(display));
    const data = { ...this.model.attributes };
    data['type_label'] = this.model.get("itm_type")==1? "Yardage": "Item";
    data['created'] = this.model.get('created').replace('T', ', ').substring(0,17);
    data['updated'] = this.model.get('updated').replace('T', ', ').substring(0,17);

    const view = formatter(data);
    this.$el.html(view);
    return;
  },
  cancelItem: function () {
    this.swapFields();
    return;
  },
  cancelKey: function (e) {
    if (e.keyCode === 13) {
      this.cancelItem();
    }
  },
  checkForm: function () {
    const data = this.el.querySelectorAll('input');
    this.validations['units'] = (this.itm_type==1)? this.validations['units_integer']:
                                                    this.validations['units_decimal']
    const changes = Backbone.Validation.checkForm(this.validations, data, this.model);
    // display errors, if any
    const dest = this.el.querySelector('div.error');
    dest.innerHTML = '';
    data.forEach(function (el) {
        if (!el.classList.contains('invalid')) return;
        const msg = el.getAttribute('data-error');
        if ( dest.innerHTML.length ) {
          dest.innerHTML = dest.innerHTML.concat('<br />');
        }
        dest.innerHTML = dest.innerHTML.concat(msg);
    });
    return changes;
  },
  editItem: function () {
    this.swapFields();
    return;
  },
  editKey: function (e) {
    if (e.keyCode === 13) {
      this.editItem();
    }
  },
  saveItem: function () {
    const changes = this.checkForm();
    if (!changes) return; //  errors found
    if (!Object.keys(changes).length) { //  no errors, but no changes
      this.cancelChange();
      return;
    }
    const opts = {
                 wait: true, view: this,
                 success: this.serverResponse
                 };
    this.model.save(changes, opts);
    return;
  },
  saveKey: function (e) {
    if (e.keyCode === 13) {
      this.saveItem();
    }
  },
  serverResponse: function (m, response, opts) {
    if ('errors' in response) {
        //  we have errors; re-display the form
        ;
    } else { //  success
      opts.view.render();
    }
    return;
  },
  setFields: function () {
    this.fields = [this.el.querySelector('div.oneButton')];
    this.fields.push(this.el.querySelector('div.twoButtons'));
    this.fields.push(this.el.querySelector('span.editUnits'));
    this.fields.push(this.el.querySelector('span.showUnits'));
    return;
  },
  swapFields: function () {
    this.fields.forEach(el => {
        el.classList.toggle('hidden');
    });
    return;
  }
});

app.stockListView = Backbone.View.extend({
  collection: new app.stockList(),
  initialize: function () {
    const templates = document.querySelectorAll('template');
    templates.forEach((tmplt) => app.templates[tmplt.id] = tmplt );
    this.collection.on('reset', this.render, this);
    this.collection.fetch({reset: true});
    return;
  },
  render: function () {
    let ct = 0;
    this.collection.models.forEach((m) => {
        const view = new app.stockItemView({model: m});
        this.el.appendChild(view.el);
        return;
    });
    return;
  }
});