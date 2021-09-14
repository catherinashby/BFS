//
Backbone.Validation = (function () {
	var lcl = {};
    var defaultPatterns = lcl.patterns = {
        // Matches any digit(s) (i.e. 0-9)
        digits: /^\d+$/,

        // Matches any number (e.g. 100.000)
        number: /^-?(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d+)?$/,

        // Matches a valid email address (e.g. mail@example.com)
        email: /^((([a-z]|\d|[!#\$%&'\*\+\-\/=\?\^_`{\|}~]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])+(\.([a-z]|\d|[!#\$%&'\*\+\-\/=\?\^_`{\|}~]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])+)*)|((\x22)((((\x20|\x09)*(\x0d\x0a))?(\x20|\x09)+)?(([\x01-\x08\x0b\x0c\x0e-\x1f\x7f]|\x21|[\x23-\x5b]|[\x5d-\x7e]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(\\([\x01-\x09\x0b\x0c\x0d-\x7f]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF]))))*(((\x20|\x09)*(\x0d\x0a))?(\x20|\x09)+)?(\x22)))@((([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])*([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])))\.)+(([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])*([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])))$/i,

        // Matches any valid url (e.g. http://www.xample.com)
        url: /^(https?|ftp):\/\/(((([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:)*@)?(((\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\.(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\.(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\.(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5]))|((([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])*([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])))\.)+(([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])*([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])))\.?)(:\d*)?)(\/((([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:|@)+(\/(([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:|@)*)*)?)?(\?((([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:|@)|[\uE000-\uF8FF]|\/|\?)*)?(\#((([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:|@)|\/|\?)*)?$/i
        };
    var defaultValidators = lcl.validators = (function(){

        // Determines whether or not a value is a number
        var isNumber = function(value){
          return _.isNumber(value) ||
                 (_.isString(value) && value.match(defaultPatterns.number));
            };
        // Determines whether or not a value is empty
        var hasValue = function(value) {
            return !(_.isNull(value) ||
                     _.isUndefined(value) ||
                     (_.isString(value) && value.trim() === '') ||
                     (_.isArray(value) && _.isEmpty(value)));
            };
        return {
            required: function(value) {
                return hasValue(value);
                },
            min: function(value, minValue) {
                return !( !isNumber(value) ||
                          (value < minValue));
                },
            max: function(value, maxValue) {
            	return !( !isNumber(value) ||
                          (value > maxValue));
                },
            range: function(value, minValue, maxValue) {
                return !( !isNumber(value) ||
                          (value > maxValue) ||
                          (value < minValue));
                },
            length: function(value, length) {
                return !( !_.isString(value) ||
                          (value.length !== length));
                },
            minLength: function(value, minLength) {
                return !( !_.isString(value) ||
                          (value.length < minLength));
                },
            maxLength: function(value, maxLength) {
                return !( !_.isString(value) ||
                          (value.length > maxLength));
                },
            rangeLength: function(value, minLength, maxLength) {
                return !( !_.isString(value) ||
                          (value.length > maxLength) ||
                          (value.length < minLength));
                },
            oneOf: function(value, valueList) {
                return _.contains(valueList, value);
                },
            pattern: function(value, pattern) {
                let ptn = defaultPatterns[pattern] || pattern;
                return !( !hasValue(value) ||
                          (!value.toString().match(ptn)));
                },
            };
        }());

	//  a 'validations' object has field/attribute names as keys,
    //  pointing to an object (or array of objects, in order of execution;
    //      first failure ends the chain) as values
    //  Keys of value-objects are:
    //      'name': a Function object used as validator, or
    //              a String: the name of a predefined validator
    //      'message': the desired error message
    //      'args': arguments needed by the validator, other than the value
    //
    //  Examples:
    //  { 'name': { 'name': 'required', 'message': 'A name is required.' },
    //    'email': [ { 'name': 'required', 'message': 'An email address is required.' },
    //               { 'name': 'email', 'message': 'Please enter a valid email address.' }
    //             ],
    //    'age': { 'name': 'min', 'args': [ 16 ],
    //             'message': 'You must be at least sixteen years old.' }
    //  }

    lcl.checkForm = function( valObj, fieldList, model ) {
        let changes = {};
        let errs = false;
        fieldList.forEach( function( elem ) {
            // does it have a name?
            if ( !elem.name )  return;
            // does the name have a validation?
            if ( elem.name in valObj )  {
                let tests = valObj[ elem.name ];
                if ( !_.isArray( tests ) ) {
                    tests = [ valObj[ elem.name ] ];
                };
                let msg = null;
                tests.forEach( function( test ) {
                    if ( msg )  return;  // error already found
                    let checker = test.name;
                    if ( _.isString( checker ) ) {
                        checker = defaultValidators[ test.name ] || null;
                    }
                    if ( _.isFunction( checker ) ) {
                        let args = test.args || [];
                        args.unshift( elem.value );
                        let rc = checker.apply( null, args );
                        if ( ! rc )  {
                            msg = test.message;
                        }
                    }
                });
                if ( msg )  {
                    errs = true;
                    elem.classList.add('invalid');
                    elem.setAttribute( 'data-error', msg );
                } else {
                    elem.classList.remove('invalid');
                    elem.removeAttribute( 'data-error' );
                }
            }
            //  is a model available for comparison/update?
            if ( model )  {
				if ( elem.name in model.attributes )  {
					let attr = model.get( elem.name );
					//  do the values match?
					if ( elem.value != attr )  {
						changes[ elem.name ] = elem.value;
					}
				}
            }
        });
        if ( errs )  changes = null;
        return changes;
        };

	return lcl;
}());
//