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

app.imageModel = Backbone.Model.extend({
    defaults: {
        id: null,
        photo: null,
        item_id: null,
        uploaded: null
    }
});

app.imageSet = Backbone.Collection.extend({
    root: null,
    model: app.imageModel,
    url: '/inventory/api/picture',
    imageTemplate: '<img src="<%= mu %><%= photo %>" alt="photo#<%= id %>"' +
                 ' height="100" width="100" />',
    parse: function (response) {
        return response.objects;
    },
    render: function () {
        if (!this.root) { return; }
        let images = '';
        const imgTmplt = _.template(this.imageTemplate);

        this.each(function (pic) {
            const attrs = _.defaults(pic.attributes, { mu: app.settings.mediaURL });
            const img = imgTmplt(attrs);
            images += img;
        });
        this.root.innerHTML = images;
    }
});

app.lineItem = Backbone.Model.extend({
    idAttribute: 'sequence'
});

app.lineItems = Backbone.Collection.extend({
    model: app.lineItem
});

app.lineItemView = Backbone.View.extend({
    tagname: 'div',
    className: 'databox',
    events: {
        'change input[type="file"]': 'fileNameHandler',
        'click span.btn[title="Add"]': 'pictureSwap',
        'click span.btn[title="Clear"]': 'pictureSwap',
        'click span.btn[title="Pictures"]': 'pictureShow',
        'click span.btn[title="Save"]': 'pictureSave',
        'keyup span.btn[title="Add"]': 'pictureSwapKey',
        'keyup span.btn[title="Clear"]': 'pictureSwapKey',
        'keyup span.btn[title="Pictures"]': 'pictureShowKey',
        'keyup span.btn[title="Save"]': 'pictureSwapKey'
    },
    initialize: function () {
        _.bindAll(this, 'fetchResponse');
        this.pictures = new app.imageSet();
        this.pictures.fetch({
            wait: true,
            data: { item: this.model.get('barcode') },
            error: this.fetchResponse,
            success: this.fetchResponse
        });
    },
    addPicture (resp) {
        if ('error' in resp) {
            const txt = resp.error;
            const node = document.createTextNode(txt);
            this.nmSpc.appendChild(node);
            return;
        }
        //  success: resp contains new model
        this.pictures.add(resp);
        this.pictures.render();
    },
    fetchResponse: function () {
            this.pictures.render();
    },
    fileNameHandler: function () {
        const imageFormats = /^([a-zA-Z0-9\s_\\.\-:])+(.jpg|.jpeg|.gif|.png|.bmp)$/;
        this.nmSpc.innerHTML = '';
        if (this.input.files.length < 1) return;
        //
        const fil = this.input.files[0];
        if (!imageFormats.test(fil.name)) {
            this.nmSpc.appendChild(document.createTextNode(fil.name +
                                     ' is not a valid image file'));
            return;
        }
        const reader = new FileReader();
        const spc = this.nmSpc;
        reader.onload = function (e) {
            const img = document.createElement('IMG');
            img.height = '100';
            img.width = '100';
            img.src = e.target.result;
            spc.appendChild(img);
        }
        reader.readAsDataURL(fil);
    },
    getCookie: function (name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    },
    pictureSave: function () {
        const data = new FormData();
        data.append('file', this.input.files[0]);
        data.append('item_id', this.model.get('barcode'));
        this.uploadFile(data);
        this.input.value = '';
        this.nmSpc.innerHTML = '';
    },
    pictureSaveKey: function (e) {
        if (e.keyCode === 13) {
            this.pictureSave();
        }
    },
    pictureSwap: function () {
        const one = this.el.querySelector('#btnOne');
        const two = this.el.querySelector('#btnTwo');
        one.classList.toggle('hidden');
        two.classList.toggle('hidden');
    },
    pictureSwapKey: function (e) {
        if (e.keyCode === 13) {
            this.pictureSwap();
        }
    },
    pictureShow: function () {
        const box = this.el.querySelector('div.imgBox');
        box.classList.toggle('hidden');
    },
    pictureShowKey: function (e) {
        if (e.keyCode === 13) {
            this.pictureShow();
        }
    },
    render: function (tmplt) {
        this.$el.html(tmplt(this.model.attributes));
        this.pictures.root = this.el.querySelector('div.gallery');
        this.nmSpc = this.el.querySelector('#fileNameSpace');
        this.input = this.el.querySelector('input[type="file"]');
        return this;
    },
    uploadFile: async function (formData) {
        //
        const token = this.getCookie('csrftoken');
        try {
        const response = await
            fetch('images/upload', {
                method: 'POST',
                body: formData,
                headers: { 'X-CSRFToken': token }
                });
            const result = await response.json();
            this.addPicture(result);
            return;
        } catch (error) {
            const txt = 'Network error -- file could not be saved';
            const node = document.createTextNode(txt);
            this.nmSpc.appendChild(node);
        }
        return;
    }
});

app.lineItemsView = Backbone.View.extend({
    template: null,
    viewSet: [],
    initialize: function () {
        this.listenTo(app.invoice, 'change', this.clearLineItems);
        //
        const ctxt = app.templates['showItemTemplate'].innerHTML;
        const tmplt = _.unescape(ctxt);
        this.template = _.template(tmplt);
    },
    addToList: function (itm) {
        const oneItem = new app.lineItem(itm.attributes);
        oneItem.set('sequence', 1 + this.collection.length);
        // add itemView to collection
        this.collection.add(oneItem);
        // display item
        const itmView = new app.lineItemView({ model: oneItem })
        const item = itmView.render(this.template);
        this.el.insertBefore(item.el, this.el.children[0]);
        this.viewSet.push(itmView);
    },
    clearLineItems: function () {
        while (this.viewSet.length) {
            const view = this.viewSet.shift();
            this.collection.remove(view.model);
            view.close();
        }
    }
});

app.purchasingView = Backbone.View.extend({
    el: '#wrapper',
    initialize: function () {
        const templates = document.querySelectorAll('template');
        templates.forEach((tmplt) => app.templates[tmplt.id] = tmplt );
        this.supView = new app.supplierListView({ el: '#supplierBox' });

        app.invoice = new app.invoiceModel();
        this.invView = new app.invoiceView({
                                            el: '#invoice',
                                            model: app.invoice
                                            });

        app.dataItem = new app.itmTmplt();
        app.detailsRecord = new Backbone.Model();
        this.inp = new app.inputView({ el: '#entryBox' });

        this.itemView = new app.itemTemplateView({
                                                  el: '#itemBox',
                                                  model: app.dataItem
                                                  });
        app.invoiceDetail = new app.lineItems();
        app.detailsView = new app.lineItemsView({
                                                 el: '#itemListBox',
                                                 collection: app.invoiceDetail
                                                });
    }
});
