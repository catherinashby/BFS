//
Backbone.View.prototype.close = function () {
  this.remove();
  this.unbind();
  if (this.onClose) {
    this.onClose();
  }
}
var app = app || {};

app.image = Backbone.Model.extend({
    defaults: {
        id: null,
        photo: null,
        uploaded: null,
        item_id: null
    }
});

app.images = Backbone.Collection.extend({
    model: app.image,
    url: '/inventory/api/picture'
});

app.imageView = Backbone.View.extend({
    className: 'photo',
    addTemplate: null,
    editTemplate: null,
    showTemplate: null,
    imageFile: null,
    imageFormats: /^([a-zA-Z0-9\s_\\.\-:])+(.jpg|.jpeg|.gif|.png|.bmp)$/,
    events: {
        'click span.btn[title="Cancel"]': 'cancelChange',
        'keyup span.btn[title="Cancel"]': 'cancelKey',
        'click span.btn[title="Edit"]': 'editImage',
        'keyup span.btn[title="Edit"]': 'editKey',
        'click span.btn[title="Save"]': 'saveChange',
        'keyup span.btn[title="Save"]': 'saveKey',
        'change input[name="image"]': 'imagePreview'
    },
    validations: {
        image: {
                name: 'pattern',
                args: [],
                message: 'Invalid image format'
                },
        item_id: [
                   { name: 'required', args: [false] },
                   {
                    name: 'pattern',
                    args: [/^\d{7}$/],
                    message: 'Please enter a seven-digit item identifier.'
                    }
                 ]
    },
    initialize: function () {
        this.validations.image.args = [this.imageFormats];
        this.listenTo(this.model, 'change', this.render);
    },
    checkForm: function () {
        let data = this.el.querySelectorAll('input,textarea');
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
        if (changes) { // validation succeeded; add image file
            const elem = this.el.querySelector('input[name="image"]');
            if (elem) {
                data = new FormData();
                data.append('file', elem.files[0]);
                changes.image = data;
            }
        }
        return changes;
    },
    addImage: function () {
        const editing = this.el.parentElement.querySelector('span.btn[title="Save"]');
        if (editing) return;

        const lv = this.renderAdd();
        const fld = lv.el.querySelector('input');
        fld.focus();
    },
    addKey: function (e) {
        if (e.keyCode === 13) {
            this.addImage();
        }
    },
    cancelChange: function () {
        const id = this.model.get('id');
        if (id) { // was editing a known image
            this.render();
        } else { // was adding a new image
            this.close();
        }
    },
    cancelKey: function (e) {
        if (e.keyCode === 13) {
            this.cancelChange();
        }
    },
    editImage: function () {
        const editing = this.el.parentElement.querySelector('span.btn[title="Save"]');
        if (editing) return;

        const lv = this.renderEdit();
        const fld = lv.el.querySelector('input');
        fld.focus();
    },
    editKey: function (e) {
        if (e.keyCode === 13) {
            this.editImage();
        }
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
    imagePreview: function () {
        const inp = this.el.querySelector('input[name="image"]');
        const imgBox = this.el.querySelector('#imagePreview');
        const regex = this.imageFormats;
        const fil = inp.files[0];
        imgBox.innerHTML = '';

        if (regex.test(fil.name.toLowerCase())) {
            this.imageFile = fil;
            const reader = new FileReader();
            reader.onload = function (e) {
                const img = document.createElement('IMG');
                img.height = '100';
                img.width = '100';
                img.src = e.target.result;
                imgBox.appendChild(img);
            }
            reader.readAsDataURL(fil);
        } else {
            const msg = document.createTextNode(
                    fil.name + ' is not a valid image file.');
            const box = document.createElement('SPAN');
            box.setAttribute('class', 'img');
            box.appendChild(msg);
            imgBox.appendChild(box);
        }
    },
    imageSave: function (imageFormData) {
        //
        const token = this.getCookie('csrftoken');
        fetch('api/picture', {
                method: 'POST',
                body: imageFormData,
                headers: { 'X-CSRFToken': token }
            }
        ).then((resp) => { return resp.json(); }
        ).then(
            (data) => {
                if ('error' in data) {
                    return {};
                    }
                this.model.set(data);
                this.collection.add(this.model);
        }).catch(
            (error) => {
                this.cancelChange();
                return {};
            });
        return;
        //
        //  const token = this.getCookie('csrftoken');
        try {
        const response = //  await
                fetch('images/upload', {
                method: 'POST',
                body: imageFormData,
                headers: { 'X-CSRFToken': token }
                });
            const result = //  await
                response.json();
            this.model.set(result);
            this.collection.add(this.model);
            return;
        } catch (error) {
            this.cancelChange();
            return {};
        }
        return;
        //
        const xhr = new XMLHttpRequest();
        //  const token = this.getCookie('csrftoken');
        xhr.onload = function () {
            const txt = JSON.parse(event.currentTarget.responseText);
            this.model.set(txt);
            this.collection.add(this.model);
            }.bind(this);
        xhr.onerror = function () {
            this.cancelChange();
            return {};
            }.bind(this);
        xhr.open('POST', 'images/upload');
        xhr.setRequestHeader('X-CSRFToken', token);
        xhr.send(imageFormData);
    },
    saveChange: function () {
        const changes = this.checkForm();
        if (!changes) return; //  errors found
        if (!Object.keys(changes).length) { //  no errors, but no changes
          this.cancelChange();
        }
        if ('image' in changes) {
            this.imageSave(changes.image);
        } else {
            const opts = {
                          wait: true,
                          view: this,
                          template: this.editTemplate,
                          success: this.serverResponse
                          };
            this.model.save(changes, opts);
        }
    },
    saveKey: function (e) {
        if (e.keyCode === 13) {
            this.saveChange();
        }
    },
    serverResponse: function (model, response, options) {
        if ('id' in response) {
            ; //  success
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
        const imgView = this.showTemplate(this.model.attributes);
        this.$el.html(imgView);
      return this;
    },
    renderAdd: function () {
        if (this.addTemplate == null) {
            const ctxt = $('#addBox').html();
            const tmplt = _.unescape(ctxt);
            this.addTemplate = _.template(tmplt);
        }
        const imgView = this.addTemplate(this.model.attributes);
        this.$el.html(imgView);
      return this;
    },
    renderEdit: function () {
        if (this.editTemplate == null) {
            const ctxt = $('#editBox').html();
            const tmplt = _.unescape(ctxt);
            this.editTemplate = _.template(tmplt);
        }
        const imgView = this.editTemplate(this.model.attributes);
        this.$el.html(imgView);
      return this;
    }
});
//
app.imagesView = Backbone.View.extend({
    el: '#wrapper',
    events: {
        'click #wrapper button[title="Add"]': 'addImage'
    },
    initialize: function (imgs) {
        this.body = this.el.querySelector('div.bodyspace');
        this.collection = new app.images(imgs);
        this.render();
    },
    addImage: function () {
        const editing = this.body.querySelector('span.btn[title="Save"]');
        if (editing) return;
//
        let fld = this.body.querySelector('div.noContent');
        if (fld) {
            this.body.removeChild(fld);
        }
        const item = new app.image();
        item.urlRoot = app.images.prototype.url;
        item.grouping = this.collection;
        const imgView = new app.imageView({
            model: item,
            collection: this.collection
        });
        const lv = imgView.renderAdd();
        fld = lv.el.querySelector('input');
        this.body.appendChild(lv.el);
        fld.focus();
    },
    render: function () {
            if (this.collection.length) {
            while (this.body.children.length) {
                this.body.removeChild(this.body.children[0]);
            }
            this.collection.each(function (item) {
                this.renderImage(item);
            }, this);
        } else {
            const nC = document.createElement('div');
            nC.setAttribute('class', 'noContent');
            nC.appendChild(document.createTextNode('No images found'));
            this.body.appendChild(nC);
        }
    },
    renderImage: function (item) {
        const imgView = new app.imageView({
            model: item
        });
        const lv = imgView.render();
        this.body.appendChild(lv.el);
    }
});
//
