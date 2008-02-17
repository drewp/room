
// The result of filter(json) on the returned json data needs to
// return a structure like this ('columns', 'data', and 'time'
// are literals, the other values are demos):
//  { columns: ['col1', 'col2'],
//    data: [{time:'iso8601 time 1', col1: 1, col2: 2},
//           {time:'iso8601 time 2', col1: 3, col2: 4},
//           ...]}



//  http://trac-hacks.org/browser/similetimelineplugin/0.10/stimeline/htdocs/js/simile/scripts/sources.js?rev=1146 has a thing to make events from sparql (and json)

// http://simile.mit.edu/issues/browse/TIMEPLOT-7 is another version
// of loadJOSN for timeplot, using a simpler column format


// todo: label the floating divs according to the original column name


Timeplot._Impl.prototype._loadExternal = function(url, callback) {
    if (this._active) {
	var tp = this;
	
	var fError = function(statusText, status, xmlhttp) {
	    alert("Failed to load data xml from " + url + "\n" + statusText);
	    tp.hideLoadingMessage();
	};
	
	var fDone = function(xmlhttp) {
	    try {
		callback(xmlhttp.responseText);
	    } catch (e) {
	        SimileAjax.Debug.exception(e);
	    } finally {
	        tp.hideLoadingMessage();
	    }
	};
	
	this.showLoadingMessage();
	window.setTimeout(function() { SimileAjax.XmlHttp.get(url, fError, fDone); }, 0);
    }
};

Timeplot._Impl.prototype.loadJSON = function(url, eventSource, filter) {
    return this._loadExternal(url, function(result) {
	 eventSource.loadJSON(eval('(' + result + ')'), filter);
    });
}

// this behaves the same; just refactored to share code with loadJSON
Timeplot._Impl.prototype.loadText = function(url, separator, eventSource, filter) {
    return this._loadExternal(url, function(result) {
	eventSource.loadText(result, separator, url, filter);
    });
};


Timeplot.DefaultEventSource.prototype.loadJSON = function(json, filter) {
    this._events.maxValues = new Array();

    var dateTimeFormat = 'iso8601';
    var parseDateTimeFunction = this._events.getUnit().getParser(dateTimeFormat);

    var added = false;

    if (filter) {
        json = filter(json);
    }

    if (json) {
        for (var i = 0; i < json.data.length; i++){
	    var row = json.data[i];

	    var cols = [];
	    for (var j in json.columns) {
		var col = json.columns[j];
		// undefined (due to a missing column) is ok; it'll be removed in ColumnSource._process
		cols.push(row[col]);
	    }

	    var evt = new Timeplot.DefaultEventSource.NumericEvent(
		parseDateTimeFunction(row.time), cols);
	    this._events.add(evt);
	    added = true;
	}
    }

    if (added) {
        this._fire("onAddMany", []);
    }
}
