//
Backbone.View.prototype.close = function () {
  this.remove();
  this.unbind();
  if (this.onClose) {
    this.onClose();
  }
}
var app = app || {};

app.location = Backbone.Model.extend({
    defaults: {
        name: null,
        identifier: null,
        description: null
    },
    idAttribute: 'identifier',
    initialize: function () {
        this.on('change:identifier', function () {
            const ds = this.get('identifier');
            this.url = '/inventory/api/location/' + ds;
            this.fetch();
        });
    }
});

app.itmTmplt = Backbone.Model.extend({
    defaults: {
        identifier: null,
       description: null,
       brand: null
//       ,'content': null
//       ,'part_unit': null
//       ,'yardage': null
//       ,'out_of_stock': null
//       ,'notes': null
    },
    idAttribute: 'identifier'
});

app.itmTmpltList = Backbone.Collection.extend({
    model: app.itmTmplt,
    url: '/inventory/api/item',
    addID: function (ident) {
        const mdl = new this.model();
        mdl.url = this.url + '/' + ident;
        mdl.fetch({
            collection: this,
            success: function (model, response, options) {
                const coll = options.collection;
                coll.add(response);
            }
        });
    }
});

app.stockRecord = Backbone.Model.extend({
    defaults: {
        itm_id: null,
        loc_id: null
    },
    idAttribute: 'itm_id',
    initialize: function () {
        this.on('change:itm_id', function () {
            const id = this.get('itm_id');
            this.url = '/inventory/api/stock/' + id;
        });
    }
});

app.dataEntry = Backbone.Model.extend({
    defaults: {
        identifier: null,
        digitstring: null,
        type: null
    },
    idAttribute: 'identifier',
    initialize: function () {
        this.on('change:digitstring', function () {
            const ds = this.get('digitstring');
            this.url = '/inventory/api/idents/' + ds;
        });
    }
});

app.locationView = Backbone.View.extend({
    el: '#locationBox',
    showTemplate: null,
    model: new app.location(),
    initialize: function () {
        this.listenTo(this.model, 'sync', this.render);
    },
    render: function () {
        if (this.showTemplate == null) {
            const ctxt = $('#showLocation').html();
            const tmplt = _.unescape(ctxt);
            this.showTemplate = _.template(tmplt);
        }
        const locView = this.showTemplate(this.model.attributes);
        this.$el.html(locView);
    }
});

app.itemTemplateView = Backbone.View.extend({
    className: 'itemTemplate',
    showTemplate: null,
    render: function () {
        if (this.showTemplate == null) {
            const ctxt = $('#showItemTemplate').html();
            const tmplt = _.unescape(ctxt);
            this.showTemplate = _.template(tmplt);
        }
        const itmView = this.showTemplate(this.model.attributes);
        this.$el.html(itmView);
      return this;
    }
});

app.itmTmpltListView = Backbone.View.extend({
    el: '#itemListBox',
    initialize: function () {
        this.collection = new app.itmTmpltList();
        this.listenTo(this.collection, 'add', this.showItem);
        this.counter = document.getElementById('itemBox');
    },
    clearCollection: function () {
        this.el.innerHTML = '';
        this.collection.reset(null);
        this.showCount();
    },
    showCount: function () {
        let plural = 's';
        if (this.collection.length === 1) {
            plural = '';
        }
        const ct = '<span>' + this.collection.length + ' item' + plural + '</span>';
        this.counter.innerHTML = ct;
    },
    showItem: function (mdl, coll) {
        const view = new app.itemTemplateView({
            model: mdl
        });
        const lv = view.render();
        this.el.insertBefore(lv.el, this.el.childNodes[0]);
        this.showCount();
    }
});

app.dataEntryView = Backbone.View.extend({
    divErr: null,
    el: '#entryBox',
    currLoc: null,
    model: new app.dataEntry(),
    events: {
        'change input[name="digitString"]': 'parseEntry'
    },
    initialize: function () {
        this.inp = this.el.querySelector('input[name="digitString"]');
        this.divErr = this.el.querySelector('div.error');
        app.locView = new app.locationView();
        app.stockRcd = new app.stockRecord();
        app.itemListView = new app.itmTmpltListView();
        this.listenTo(this.model, 'sync', this.checkReturned);
    },
    checkReturned: function (model, response, options) {
            const ident = model.get('identifier');
            const typ = model.get('type');
            let msg;
            switch (typ) {
                case 'ITM':
                    if (!this.currLoc) {
                        msg = 'Please enter a location ID';
                        this.showError(msg);
                        break;
                    }
                    app.itemListView.collection.addID(ident);
                    app.stockRcd.set('itm_id', ident);
                    app.stockRcd.save();
                    break;
                case 'LOC':
                    this.currLoc = ident;
                    app.locView.model.set('identifier', ident);
                    app.stockRcd.set('loc_id', ident);
                    app.itemListView.clearCollection();
                    break;
                default:
                    msg = "Identifier '" + model.get('digitstring') +
                        "' was not found"
                    this.showError(msg);
            }
    },
    parseEntry: function () {
        this.divErr.innerHTML = '';
        const ds = this.inp.value || '';
        if (!/^\d+$/.test(ds)) {
            this.showError('Please enter only digits');
            return;
        }
        this.model.set('digitstring', ds);
        this.model.fetch();
    },
    showError: function (msg) {
        this.divErr.innerHTML = msg;
    }
});
