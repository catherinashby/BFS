//
Backbone.View.prototype.close = function(){
  this.remove();
  this.unbind();
  if (this.onClose){
    this.onClose();
  }
}
var app = app || {};

app.locID = Backbone.Model.extend({
    defaults: {
        'barcode': null
    },
    idAttribute: 'barcode'
});

app.location = Backbone.Model.extend({
    defaults: {
        'name': null,
        'barcode': null,
        'description': null,
        'locID': null
    },
    idAttribute: 'barcode'
});

app.shelves = Backbone.Collection.extend({
    model: app.location,
    url: '/inventory/api/location'
});

app.locationView = Backbone.View.extend({
    className: 'location',
    editTemplate: null,
    showTemplate: null,
    events: {
        'click span.btn[title="Cancel"]': 'cancelChange',
        'click span.btn[title="Edit"]': 'editLocation',
        'click span.btn[title="Print"]': 'printLocation',
        'click span.btn[title="Save"]': 'saveChange',
    },
    initialize: function () {
        this.listenTo(this.model, 'change', this.render);
        return;
    },
    cancelChange: function()    {
        var bc = this.model.get('barcode');
        if ( bc == "" ) {   // was adding a new location
            this.close();
        } else {    // was editing a known location
            this.render();
        }
    },
    editLocation: function ()   {
        var editing = this.el.parentElement.querySelector('span.btn[title="Save"]');
        if (editing)   return;

        var lv = this.renderEdit();
        fld = lv.el.querySelector("input");
        fld.focus();
        return;
    },
    printLocation: function()    {
        var bc = this.model.get('barcode')
        // locid = /identifier/<int:pk>
        // GET /inventory/api/identifier/<int:pk>
        this.model.save(null, {'patch':true,'wait':true});
        return
    },
    saveChange: function()    {
        var bc = this.model.get('barcode');
        var name = this.el.querySelector('input').value;
        var desc = this.el.querySelector('textarea').value;
        this.model.set({'name': name, 'description': desc});
        if ( this.model.isNew() ) {
            this.collection.add(this.model);
        }
        this.model.save( null, null, {'wait': true});
        return;
    },
    render: function() {
        if (this.showTemplate == null)  {
            var ctxt = $('#showBox').html();
            var tmplt = _.unescape( ctxt );
            this.showTemplate = _.template( tmplt );
        }
        var locView = this.showTemplate( this.model.attributes );
        this.$el.html( locView );
      return this;
    },
    renderEdit: function() {
        if (this.editTemplate == null)  {
            var ctxt = $('#editBox').html();
            var tmplt = _.unescape( ctxt );
            this.editTemplate = _.template( tmplt );
        }
        var locView = this.editTemplate( this.model.attributes );
        this.$el.html( locView );
      return this;
    }
})
//
app.shelvesView = Backbone.View.extend({
    el: '#wrapper',
    events: {
        'click #wrapper button[title="Add"]': 'addLocation'
    },
    initialize: function(locs)   {
        this.body = this.el.querySelector('div.bodyspace');
        this.collection = new app.shelves(locs);
        this.render();
    },
    addLocation: function() {
        var editing = this.body.querySelector('span.btn[title="Save"]');
        if (editing)   return;
//
        var fld = this.body.querySelector('div.noContent');
        if ( fld )  {
            this.body.removeChild( fld );
        }
        var item = new app.location();
        var locView = new app.locationView({
			model: item,
            collection: this.collection
        });
        var lv = locView.renderEdit();
        fld = lv.el.querySelector('input');
        this.body.appendChild( lv.el );
        fld.focus();
    },
    render: function()  {
        if (this.collection.length) {
            while (this.body.children.length)   {
                this.body.removeChild(this.body.children[0]);
            }
            this.collection.each(function( item ) {
                this.renderLocation( item );
            }, this );
        } else {
            var nC = document.createElement('div');
            nC.setAttribute('class', 'noContent');
            nC.appendChild(document.createTextNode('No locations found'));
            this.body.appendChild( nC );
        }
    },
    renderLocation: function( item )    {
        var locView = new app.locationView({
			model: item
        });
        var lv = locView.render();
        this.body.appendChild( lv.el );
    }
});
//
var stop = "here";
//
