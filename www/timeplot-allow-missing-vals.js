
// patched to allow undefined values, which are then omitted from the ColumnSource._data
Timeplot.ColumnSource.prototype._process = function() {
    var count = this._eventSource.getCount();
    var times = new Array(count);
    var values = new Array(count);
    var min = Number.MAX_VALUE;
    var max = Number.MIN_VALUE;
    var i = 0;
    var iterator = this._eventSource.getAllEventIterator();
    while (iterator.hasNext()) {
        var event = iterator.next();
        var time = event.getTime();
	var value = this._getValue(event);
	if (value != undefined && !isNaN(value)) {
	    if (value < min) {
		min = value;
	    }
	    if (value > max) {
		max = value;
	    }    
	    times[i] = time;
	    values[i] = value;
	    i++;
	} 
    }
    times.length = i;
    values.length = i;
    this._data = {
        times: times,
        values: values
    };
    if (max == Number.MIN_VALUE) max = 1;  
    this._range = {
        earliestDate: this._eventSource.getEarliestDate(),
        latestDate: this._eventSource.getLatestDate(),
        min: min,
        max: max
    };
}

// patched to passthru undefined values
Timeplot.ColumnSource.prototype._getValue = function(event) {
    var v = event.getValues()[this._column];
    if (v == undefined) {
	return undefined;
    }
    return parseFloat(v);
}

