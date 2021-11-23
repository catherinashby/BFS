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
    validations: {
        'name': { 'name': 'required', 'message': 'A name is required.' }
    },
    initialize: function () {
        this.listenTo(this.model, 'change', this.render);
        return;
    },
    checkForm: function()    {
        var data = this.el.querySelectorAll('input,textarea');
        var changes = Backbone.Validation.checkForm( this.validations, data, this.model );
        var src = this.el.querySelector( 'input.invalid' );
        var dest = this.el.querySelector('div.error');
        var msg = src ? src.getAttribute( 'data-error' ): '';
        dest.innerHTML = msg;
        return changes;
    },
    cancelChange: function()    {
        var bc = this.model.get('barcode');
        if ( bc )   {    // was editing a known location
            this.render();
        } else {        // was adding a new location
            this.close();
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
        this.model.save(null, {'patch':true,'wait':true});
        return
    },
    saveChange: function()    {
        var changes = this.checkForm();
        if ( !changes )  return;            //  errors found
        if ( !Object.keys(changes).length )  {  //  no errors, but no changes
          this.cancelChange();
          return;
        }
        opts = { 'wait': true, 'view': this,
                'template': this.editTemplate,
                'success': this.serverResponse };
        this.model.save(changes, opts);
        return;
    },
    serverResponse: function( model, response, options )  {
        if ( 'locID' in response ) {    //  success
            let isNew = ( model._previousAttributes.locID == null );
            if ( isNew )    {
                model.grouping.add( model );
            }
        } else {
            //  we have errors; re-display the form
            options.view.$el.html( options.template(model.attributes) );
            var box = options.view.el;
            var errs = response.errors;
//
            for ( var fld in errs ) {
                let msg = errs[fld];
                let selector = 'input[name="' + fld + '"]';
                let src = box.querySelector( selector );
                src.classList.add( 'invalid' );
                src.setAttribute( 'data-error', msg );
                let dest = box.querySelector('div.error');
                dest.innerHTML = msg;
                //  reset the model to last correct value
                model.attributes[fld] = model._previousAttributes[fld];
            }
        }
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
        item.urlRoot = app.shelves.prototype.url;
        item.grouping = this.collection;
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
