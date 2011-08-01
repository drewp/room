
$(function () {
    $(".services").load("/nagios/cgi-bin/status.cgi?host=all&servicestatustypes=28 table.status", function () {
	$(window).trigger("relayout");
    });

    $("#recentExpand").click(function () { 
	$(this).text("V");
	$(this).parent().next().show();
	$("#recentVisitors").load("/activity/f/netVisitors.xhtml?order=desc");
    });

    $("input[name=msg]").keyup(function () {
	var chars = $("form[action=microblogUpdate] input[type=text]").val().length;
	$("#blogChars").text("("+chars+")");
    });


    function TempGraph() {
	var self=this;
	var graphImg = $(".graphLayout img");
	self.hours = 26;
	this.setImgSrc = function() {
	    graphImg.attr(
		"src", "http://graphite.bigasterisk.com/render/?"+
		    $.param({
			width: "240", height: "250",
			target: ["system.house.temp.downstairs",
				 "system.house.temp.ariroom",
				 "keepLastValue(system.house.temp.bedroom)",
				 "system.house.temp.livingRoom",
				 "system.noaa.ksql.temp_f",
				 "system.house.temp.frontDoor"],
			from: "-"+self.hours+"hours",
			hideAxes: "false",
			hideLegend: "true",
			lineWidth: "1.5",
			yMin: "40", yMax: "90",
		    }, true));
	}

	self.setImgSrc();
	$("input[name=tempHours]").click(function () {
	    self.hours = $("input[name=tempHours]:checked").attr("value");
	    self.setImgSrc();
	});
	$("#th3")[0].checked = true;
    }
    var t=new TempGraph();

/*
nowjs not working yet
    now.updateMsg = function (main, bot) {
	$("#frontDoorLcd").val(main);
	$("#frontDoorBottomLine").val(bot);
	// restore cursor position if they were editing?
    }
    $("#frontDoorLcd").keyup(function () { now.editedMain($(this).val()); });
*/

    (function () {
// needs to route to frontdoormsg instead, who could probably render this whole widget
	$.get("frontDoor/lcd/lastLine", function (data){ $("#frontDoorLastLine").val(data) });
	var fd = $("#frontDoorLcd")
	$.get("frontDoor/lcd", function (data){ fd.val(data) });
	
	fd.keyup(function() {
	    $("#frontDoorSave").css("color", "yellow");
	    $.post("frontDoor/lcd", {message: fd.val()}, function () {
		$("#frontDoorSave").css("color", "black");
	    });
	});
    })();

    function isotopeSections() {
	var iso = $('#sections').isotope({
	    itemSelector : '.section',
	    layoutMode : 'masonry'
	});
	$(window).bind("relayout", function () { iso.isotope("reLayout"); });
    }	
    $(".col2").isotope({
	itemSelector: "div",
	layoutMode: 'fitRows',
    });

    if (notPhone) {
	isotopeSections();
    }
});