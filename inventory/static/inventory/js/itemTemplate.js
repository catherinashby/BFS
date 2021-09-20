//
Backbone.View.prototype.close = function(){
  this.remove();
  this.unbind();
  if (this.onClose){
    this.onClose();
  }
}
var app = app || {};

app.itmTmplt = Backbone.Model.extend({
    defaults: {
        'description': null,
        'barcode': null,
        'brand': null,
        'content': null,
        'part_unit': null,
        'yardage': null,
        'notes': null,
        'itmID': null,
        'linked_code': null
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
        'keyup span.btn[title="Save"]': 'saveKey',
    },
    validations: {
        'description': { 'name': 'required', 'message': 'A description is required.' }
    },
    initialize: function () {
        this.listenTo(this.model, 'change', this.render);
        return;
    },
    cancelChange: function()    {
        var bc = this.model.get('barcode');
        if ( bc )   {    // was editing a known itemTemplate
            this.render();
        } else {        // was adding a new itemTemplate
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
        var data = this.el.querySelectorAll('input,textarea');
        var changes = Backbone.Validation.checkForm( this.validations, data, this.model );
        // show errors
        var src = this.el.querySelector( 'input.invalid' );
        var dest = this.el.querySelector('div.error');
        var msg = src ? src.getAttribute( 'data-error' ): '';
        dest.innerHTML = msg;
        //  extra tests
        if ( changes )  {
            var ydg = this.el.querySelector('#ydg').checked? 'True': 'False';
            if ( this.model.get('yardage') !== ydg )    {
                changes['yardage'] = ydg;
            }
        }
        return changes;
    },
    editItemTemplate: function()    {
        var editing = this.el.parentElement.querySelector('span.btn[title="Save"]');
        if (editing)   return;

        var lv = this.renderEdit();
        fld = lv.el.querySelector("input[name='description']");
        fld.focus();
        return;
    },
    editKey: function(e)   {
        if ( e.keyCode == 13 )  {
            this.editItemTemplate();
        }
        return;
    },
    printItemTemplate: function()    {
        this.model.save(null, {'patch':true,'wait':true});
        return
    },
    printKey: function(e)   {
        if ( e.keyCode == 13 )  {
            this.printItemTemplate();
        }
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
        var itmView = this.showTemplate( this.model.attributes );
        this.$el.html( itmView );
      return this;
    },
    renderEdit: function()    {
        if (this.editTemplate == null)  {
            var ctxt = $('#editBox').html();
            var tmplt = _.unescape( ctxt );
            this.editTemplate = _.template( tmplt );
        }
        var ydg = this.model.get('yardage');
        var itmView = this.editTemplate( this.model.attributes );
        this.$el.html( itmView );
        if ( ydg == "True" )    {
            var inp = this.el.querySelector('#ydg');
            inp.setAttribute('checked', 'checked' );
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
    initialize: function(items)   {
        this.body = this.el.querySelector('div.bodyspace');
        this.collection = new app.itmTmpltList(items);
        this.render();
    },
    addItemTemplate: function() {
        var editing = this.body.querySelector('span.btn[title="Save"]');
        if (editing)   return;
//
        var fld = this.body.querySelector('div.noContent');
        if ( fld )  {
            this.body.removeChild( fld );
        }
        var item = new app.itmTmplt();
        var tmpltView = new app.itmTmpltView({
			model: item,
            collection: this.collection
        });
        var lv = tmpltView.renderEdit();
        fld = lv.el.querySelector("input[name='description']");
        this.body.appendChild( lv.el );
        fld.focus();
    },
    render: function()  {
        if (this.collection.length) {
            while (this.body.children.length)   {
                this.body.removeChild(this.body.children[0]);
            }
            this.collection.each(function( item ) {
                this.renderItemTemplate( item );
            }, this );
        } else {
            var nC = document.createElement('div');
            nC.setAttribute('class', 'noContent');
            nC.appendChild(document.createTextNode('No items found'));
            this.body.appendChild( nC );
        }
    },
    renderItemTemplate: function( item )    {
        var tmpltView = new app.itmTmpltView({
			model: item
        });
       var lv = tmpltView.render();
        this.body.appendChild( lv.el );
    }
});
//
