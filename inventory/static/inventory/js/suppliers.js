//
Backbone.View.prototype.close = function(){
  this.remove();
  this.unbind();
  if (this.onClose){
    this.onClose();
  }
}
var app = app || {};

app.supplier = Backbone.Model.extend({
    defaults: {
        'id': null,
        'name': null,
        'street': null,
        'street_ext': null,
        'city': null,
        'state': null,
        'zip5': null,
        'phone_1': null,
        'phone_2': null,
        'notes': null
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
        'keyup span.btn[title="Save"]': 'saveKey',
    },
    validations: {
        'name': { 'name': 'required', 'message': 'A name is required.' },
        'zip5': { 'name': 'pattern', 'args': [ /^\d{5}$/ ],
                  'message': 'Please enter a five-digit zipcode.' },
        'phone_1': [
                   { 'name': 'required', 'args': [ false ] },
                   { 'name': 'pattern', 'message': 'Enter a 7- or 10-digit number',
                     'args': [ /^(\(?(\d{3})\)?[- ]?)?(\d{3})[- ]?(\d{4})$/ ] }
                   ],
        'phone_2': [
                   { 'name': 'required', 'args': [ false ] },
                   { 'name': 'pattern', 'message': 'Enter a 7- or 10-digit number',
                     'args': [ /^(\(?(\d{3})\)?[- ]?)?(\d{3})[- ]?(\d{4})$/ ] }
                   ]
    },
    initialize: function () {
        this.listenTo(this.model, 'change', this.render);
        return;
    },
    cancelChange: function()    {
        var num = this.model.get('id');
        if ( num )   {    // was editing a known supplier
            this.render();
        } else {        // was adding a new supplier
            this.close();
        }
    },
    cancelKey: function(e)   {
        if ( e.keyCode == 13 )  {
            this.cancelChange();
        }
        return;
    },
    checkForm: function()    {
        var data = this.el.querySelectorAll( 'input,textarea' );
        var changes = Backbone.Validation.checkForm( this.validations, data, this.model );
        // display errors, if any
        var dest = this.el.querySelectorAll( 'div.error' );
        dest.forEach(function(el) { el.innerHTML = ''; });
        data.forEach(function(el) {
            if ( !el.classList.contains( 'invalid' ) )  return;
            var msg = el.getAttribute( 'data-error' );
            dest = el.parentElement.querySelector( 'div.error' );
            dest.innerHTML = msg;
        });
        return changes;
    },
    editKey: function(e)   {
        if ( e.keyCode == 13 )  {
            this.editSupplier();
        }
        return;
    },
    editSupplier: function()    {
        var editing = this.el.parentElement.querySelector('span.btn[title="Save"]');
        if (editing)   return;

        var lv = this.renderEdit();
        fld = lv.el.querySelector("input[name='name']");
        fld.focus();
        return;
    },
    saveChange: function()    {
        var changes = this.checkForm();
        if ( !changes )  return;        //  errors found
        if ( !Object.keys(changes).length )  {  //  no errors, but no changes
          this.cancelChange();
          return;
        }
        this.model.set(changes);
        if ( this.model.isNew() ) {
            this.collection.add(this.model);
        }
        this.model.save( null, null, {'wait': true});
        return;
    },
    saveKey: function(e)   {
        if ( e.keyCode == 13 )  {
            this.saveChange();
        }
        return;
    },
    render: function()    {
        if (this.showTemplate == null)  {
            var ctxt = $('#showBox').html();
            var tmplt = _.unescape( ctxt );
            this.showTemplate = _.template( tmplt );
        }
        var supView = this.showTemplate( this.model.attributes );
        this.$el.html( supView );
      return this;
    },
    renderEdit: function()    {
        if (this.editTemplate == null)  {
            var ctxt = $('#editBox').html();
            var tmplt = _.unescape( ctxt );
            this.editTemplate = _.template( tmplt );
        }
        var supView = this.editTemplate( this.model.attributes );
        this.$el.html( supView );
      return this;
    }
});

app.supplierListView = Backbone.View.extend({
    el: '#wrapper',
    events: {
        'click #wrapper button[title="Add"]': 'addSupplier'
    },
    initialize: function(sups)  {
        this.body = this.el.querySelector('div.bodyspace');
        this.collection = new app.supplierList(sups);
        this.render();
    },
    addSupplier: function()  {
        var editing = this.body.querySelector('span.btn[title="Save"]');
        if (editing)   return;
//
        var fld = this.body.querySelector('div.noContent');
        if ( fld )  {
            this.body.removeChild( fld );
        }
        var item = new app.supplier();
        var supView = new app.supplierView({
			model: item,
            collection: this.collection
        });
        var lv = supView.renderEdit();
        fld = lv.el.querySelector('input[name="name"]');
        this.body.appendChild( lv.el );
        fld.focus();
    },
    render: function()  {
        if (this.collection.length) {
            while (this.body.children.length)   {
                this.body.removeChild(this.body.children[0]);
            }
            this.collection.each(function( item ) {
                this.renderSupplier( item );
            }, this );
        } else {
            var nC = document.createElement('div');
            nC.setAttribute('class', 'noContent');
            nC.appendChild(document.createTextNode('No suppliers found'));
            this.body.appendChild( nC );
        }
    },
    renderSupplier: function(item)  {
        var supView = new app.supplierView({
			model: item
        });
        var lv = supView.render();
        this.body.appendChild( lv.el );
    }
});

//
