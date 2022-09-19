//
Backbone.View.prototype.close = function(){
  this.remove();
  this.unbind();
  if (this.onClose){
    this.onClose();
  }
}
var app = app || {};

app.location = Backbone.Model.extend({
    defaults: {
        'name': null,
        'identifier': null,
        'description': null
    },
    idAttribute: 'identifier',
    initialize: function()  {
        this.on("change:identifier", function() {
            var ds = this.get('identifier');
            this.url = '/inventory/api/location/' + ds;
            this.fetch();
        });
    }
});

app.itmTmplt = Backbone.Model.extend({
    defaults: {
        'identifier': null
       ,'description': null
       ,'brand': null
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
    addID: function(ident)   {
        let mdl = new this.model();
        mdl.url = this.url + '/' + ident;
        mdl.fetch({
            'collection': this,
            'success':function(model, response, options){
                let coll = options.collection;
                coll.add(response);
            }
        });
        return;
    }
});

app.dataEntry = Backbone.Model.extend({
    defaults: {
        'identifier': null,
        'digitstring': null,
        'type': null
    },
    idAttribute: 'identifier',
    initialize: function()  {
        this.on("change:digitstring", function() {
            var ds = this.get('digitstring');
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
        return;
    },
    render: function() {
        if (this.showTemplate == null)  {
            var ctxt = $('#showLocation').html();
            var tmplt = _.unescape( ctxt );
            this.showTemplate = _.template( tmplt );
        }
        var locView = this.showTemplate( this.model.attributes );
        this.$el.html( locView );
      return;
    }
});

app.itemTemplateView = Backbone.View.extend({
    className: 'itemTemplate',
    showTemplate: null,
    render: function() {
        if (this.showTemplate == null)  {
            var ctxt = $('#showItemTemplate').html();
            var tmplt = _.unescape( ctxt );
            this.showTemplate = _.template( tmplt );
        }
        var itmView = this.showTemplate( this.model.attributes );
        this.$el.html( itmView );
      return this;
    }
});

app.itmTmpltListView = Backbone.View.extend({
    el: '#itemListBox',
    initialize: function()   {
        this.collection = new app.itmTmpltList();
        this.listenTo(this.collection, 'add', this.showItem);
        this.counter = document.getElementById('itemBox');
    },
    clearCollection: function() {
        this.el.innerHTML = '';
        this.collection.reset(null);
        this.showCount();
        return;
    },
    showCount:  function()  {
        let plural = 's';
        if ( this.collection.length == 1 )  {
            plural = '';
        }
        let ct = '<span>'+ this.collection.length + ' item' + plural +'</span>';
        this.counter.innerHTML = ct;
    },
    showItem: function(mdl, coll)    {
        let view = new app.itemTemplateView({
            model: mdl
        });
        let lv = view.render();
        this.el.insertBefore(lv.el, this.el.childNodes[0]);
        this.showCount();
        return;
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
    initialize: function()  {
        this.inp = this.el.querySelector('input[name="digitString"]');
        this.divErr = this.el.querySelector('div.error');
        app.locView = new app.locationView();
        app.itemListView = new app.itmTmpltListView();
        this.listenTo(this.model, 'sync', this.checkReturned);
        return;
    },
    checkReturned: function(model, response, options)   {
            var ident = model.get('identifier');
            var typ = model.get('type');
            switch (typ) {
                case 'ITM':
                    if (!this.currLoc)   {
                        var msg = "Please enter a location ID";
                        this.showError(msg);
                        break;
                    }
                    app.itemListView.collection.addID(ident);
                    break;
                case 'LOC':
                    this.currLoc = ident;
                    app.locView.model.set('identifier', ident);
                    app.itemListView.clearCollection();
                    break;
                default:
                    var msg = "Identifier '" + model.get('digitstring')
                        + "' was not found"
                    this.showError(msg);
            }
        return;
    },
    parseEntry: function()  {
        this.divErr.innerHTML = "";
        var ds = this.inp.value || "";
        if ( ! /^\d+$/.test(ds) )   {
            this.showError("Please enter only digits");
            return;
        }
        this.model.set("digitstring", ds);
        this.model.fetch();
        return;
    },
    showError: function(msg)    {
        this.divErr.innerHTML = msg;
        return;
    }
});
