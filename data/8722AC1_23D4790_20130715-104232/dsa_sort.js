// This code originally comes from:
// http://www.kryogenix.org/code/browser/sorttable/

// 2004-12-03: Modifications by mcramer@pbs.org: http://blog.webkist.com/archives/000043.html
// 2005-01-07: Modifications by Anthony.Garrett@aods.org (tested IE 6.0.28, Opera 7.54, Firefox 1.0)
//             [Problem: Firefox 1.0 won't display the span style for the up and down arrows.]
// 2005-01-11: Anthony.Garrett@aods.org Fixed small bug:
//             Error occurred when clicking on column header link just to the right of the text.
// 2005-01-11: mcramer@pbs.org integrated AG's fixes and added support for <select> sorting.
// 2005-01-13: mcramer@pbs.org: Caching optimizations. Should be faster on big tables.
// 2005-04-29: mcramer@pbs.org: Style fix, "nosort" stuff, and don't link empty headers.

addEvent(window, "load", sortables_init);

var SORT_COLUMN_INDEX;

function sortables_init() {
    // Find all tables with class sortable and make them sortable
    if (!document.getElementsByTagName)
	return;
    tbls = document.getElementsByTagName("table");
    for (ti = 0; ti < tbls.length; ti++) {
	thisTbl = tbls[ti];
	if (((' ' + thisTbl.className + ' ').indexOf(" sortable ") != -1) && (thisTbl.id)) {
	    ts_makeSortable(thisTbl);
	}
    }
    alternate( thisTbl.id );
}

function ts_makeSortable(table) {
    var firstRow;
    for (var i = 0; i < table.rows.length; i++) {
	firstRow = table.rows[i];
	if (firstRow.cells && firstRow.cells[0].nodeName == "TD") {
	    firstRow = table.rows[i - 1];
	    break;
	}
    }

    if (!firstRow)
	return;

    // We have a first row: assume it's the header, and make its contents clickable links
    for (var i = 0; i < firstRow.cells.length; i++) {
	var cell = firstRow.cells[i];
	if(cell.childNodes.length > 0 && cell.className.indexOf("nosort") == -1) {
	    var link = document.createElement("a");
	    link.href = "#";
	    link.style.textDecoration = "none";
	    link.className = "sortheader";	// AG Added (makes the styling work)
	    addEvent(link, "click", ts_resortTable);
	    var l = cell.childNodes.length;
	    while (cell.childNodes.length > 0) {
	        link.appendChild(cell.childNodes[0]);
  	    }
	    var span = document.createElement("span");
	    span.className = "sortarrow";
	    span.innerHTML = '&nbsp;&nbsp;';
  	    link.appendChild(span);
	    cell.appendChild(link);
	}
    }
}

function ts_getInnerText(el) {
    if (typeof el == "string" || typeof el == "undefined")
	return el;

    if(el.ts_allText)
      return el.ts_allText;

    var str = new Array();
    var cs = el.childNodes;

    for (var i = 0; i < cs.length; i++) {
	switch (cs[i].nodeType) {
	  case 1: // ELEMENT_NODE
	        str.push(ts_getInnerText(cs[i]));
	      break;
	  case 3: // TEXT_NODE
	      str.push(cs[i].nodeValue);
	      break;
	}
    }
    // Save the extracted text for later. This costs the client RAM,
    // but saves major CPU when the cell contents are particularly
    // complex.
    return el.ts_allText = str.join(" ");
}

function ts_resortTable(event) {
    var lnk = event.currentTarget ? event.currentTarget : event.srcElement;
    // AG - IE doesn't support "currentTarget", must use "srcElement" instead.
    // get the span
    var span;
    if(lnk.tagName && lnk.tagName.toLowerCase() == 'span')
      span = lnk;
    else {
      for (var ci=0; ci<lnk.childNodes.length; ci++) {
        if(lnk.childNodes[ci].tagName && lnk.childNodes[ci].tagName.toLowerCase() == 'span')
            span = lnk.childNodes[ci];
      }
    }
    var td = lnk.parentNode;
    while(td.tagName != 'TD' && td.tagName != 'TH')
      td = td.parentNode;

    var column = td.cellIndex;
    var table = getParent(td, 'TABLE');

    var nonHeaderIndex;
    for (nonHeaderIndex = 0; nonHeaderIndex < table.rows.length; nonHeaderIndex++) {
	if(table.rows[nonHeaderIndex].cells &&
	   table.rows[nonHeaderIndex].cells[0].nodeName == "TD") {
	  break;
	}
    }

    // If 0, the table has no rows. If >= table.rows.length, it has no data.
    if(nonHeaderIndex == 0 || nonHeaderIndex >= table.rows.length)
      return;

    // Work out a type for the column
    var itm = ts_getInnerText(table.rows[nonHeaderIndex].cells[column]);

    // A date in dd/mm/yyyy hh:mm:ss format.
    if (itm.match(/^\d\d[\/-]\d\d[\/-]\d\d\d\d\s\d\d:\d\d:\d\d$/))
        sortfn = ts_sort_date

    // 23468
    else if (itm.match(/^\d+$/))
        sortfn = ts_sort_numeric

    // Everything else.
    else
        sortfn = ts_sort_caseinsensitive

    SORT_COLUMN_INDEX = column;

    var newRows = new Array();
    for (var j=nonHeaderIndex; j<table.rows.length; j++) {
	newRows[j - nonHeaderIndex] = table.rows[j];
    }

    newRows.sort(sortfn);

    if (span.getAttribute("sortdir") == 'down') {
	ARROW = '&nbsp;&uarr;';
	newRows.reverse();
	span.setAttribute('sortdir', 'up');
    } else {
	ARROW = '&nbsp;&darr;';
	span.setAttribute('sortdir', 'down');
    }

    // We appendChild rows that already exist to the tbody, so it moves them rather 
    // than creating new ones don't do sortbottom rows
    for (var i=0; i<newRows.length; i++) {
	if (!newRows[i].className ||
	    (newRows[i].className &&
	     (newRows[i].className.indexOf('sortbottom') == -1)))
	    table.tBodies[0].appendChild(newRows[i]);
    }
    // do sortbottom rows only
    for (i = 0; i < newRows.length; i++) {
	if (newRows[i].className &&
	    (newRows[i].className.indexOf('sortbottom') != -1))
	    table.tBodies[0].appendChild(newRows[i]);
    }
    // Delete any other arrows there may be showing
    var allspans = document.getElementsByTagName("span");
    for (var ci = 0; ci < allspans.length; ci++) {
	if (allspans[ci].className == 'sortarrow') {
	    if (getParent(allspans[ci], "table") == getParent(lnk, "table")) {	// in the same table as us?
		allspans[ci].innerHTML = '&nbsp;&nbsp;';
	    }
	}
    }
    span.innerHTML = ARROW;

    alternate( table.id );
    //event.preventDefault();
}

function getParent(el, pTagName) {
    if (el == null)
	return null;
    else if (el.nodeType == 1 && el.tagName.toLowerCase() == pTagName.toLowerCase())	// Gecko bug, supposed to be uppercase
	return el;
    else
	return getParent(el.parentNode, pTagName);
}

function ts_sort_date(a, b) {

    aa = ts_getInnerText(a.cells[SORT_COLUMN_INDEX]);
    bb = ts_getInnerText(b.cells[SORT_COLUMN_INDEX]);
	
	var dt1=new Date(aa);
	var dt2=new Date(bb);

    //aaBits = aa.split(/\/|-| |:/);

	//if (bb.length == 19) {
	//	dt1 = aa.substr(6, 4) + aa.substr(3, 2) + aa.substr(0, 2);
	//}
	//else
	//	return 0;

    //bbBits = bb.split(/\/|-| |:/);
    
    //if (bb.length == 19) {
	//	dt2 = bb.substr(6, 4) + bb.substr(3, 2) + bb.substr(0, 2);
    //} 
    //else
	//	return 0;

    if (dt1 == dt2)
	return 0;
    if (dt1 < dt2)
	return -1;
    return 1;
}

function ts_sort_numeric(a, b) {
    aa = parseFloat(ts_getInnerText(a.cells[SORT_COLUMN_INDEX]));
    if (isNaN(aa))
	aa = 0;
    bb = parseFloat(ts_getInnerText(b.cells[SORT_COLUMN_INDEX]));
    if (isNaN(bb))
	bb = 0;
    return aa - bb;
}

function ts_sort_caseinsensitive(a, b) {
    aa = ts_getInnerText(a.cells[SORT_COLUMN_INDEX]).toLowerCase();
    bb = ts_getInnerText(b.cells[SORT_COLUMN_INDEX]).toLowerCase();
    if (aa == bb)
	return 0;
    if (aa < bb)
	return -1;
    return 1;
}

function ts_sort_default(a, b) {
    aa = ts_getInnerText(a.cells[SORT_COLUMN_INDEX]);
    bb = ts_getInnerText(b.cells[SORT_COLUMN_INDEX]);
    if (aa == bb)
	return 0;
    if (aa < bb)
	return -1;
    return 1;
}

function addEvent(elm, evType, fn, useCapture) {
// addEvent cross-browser event handling for IE5+,  NS6 and Mozilla
// By Scott Andrew
    if (elm.addEventListener) {
	elm.addEventListener(evType, fn, useCapture);
	return true;
    } else if (elm.attachEvent) {
	var r = elm.attachEvent("on" + evType, fn);
	return r;
    } else {
	alert("Handler could not be added");
    }
}

function alternate( id ) 
{
	var table = document.getElementById( id );		
	var rows  = table.getElementsByTagName( 'tr' );	
		
	// start count @ 1 to prevent striping of header row
	for ( i = 1; i < rows.length; i++ ) 
	{						
	    if ( i % 2 == 0 )
	        rows[i].className = 'bg0';
	    else
	        rows[i].className = 'bg1';
	}
}

// Suggested by MT Jordan:
// Posted by liorean at http://codingforums.com
// IE5 triggers runtime error w/o push function
// Shortened by mcramer@pbs.org

if (typeof Array.prototype.push == 'undefined') {
    Array.prototype.push = function() {
        var b = this.length;
        for(var i=0; i<arguments.length; i++ ) {
            this[b + i] = arguments[i];
        }
        return this.length
    }
}

