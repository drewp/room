
$(function () {
    $(".services").load("/nagios/cgi-bin/status.cgi?host=all&servicestatustypes=28 table.status");

    function renderTomato(tomatoResult, target) {
	var arplist, wlnoise, dhcpd_static, wldev, dhcpd_lease;
	eval(tomatoResult);

	var aboutIp = {};
	var byMac = {};

	$.each(arplist, function (i, r) {
	    var ip=r[0];
	    if (aboutIp[ip] == undefined) { aboutIp[ip] = {}; }
	    aboutIp[ip]['mac'] = r[1];
	    byMac[r[1]] = aboutIp[ip];
	    aboutIp[ip]['interface'] = r[2];

	});
	$.each(dhcpd_lease, function (i, r) {
	    var ip=r[1];
	    if (aboutIp[ip] == undefined) { aboutIp[ip] = {}; }
	    aboutIp[ip]['name'] = r[0];
	    aboutIp[ip]['mac'] = r[2];
	    byMac[r[2]] = aboutIp[ip];
	    aboutIp[ip]['lease'] = r[3];
	});
	$.each(wldev, function (i, r) {
	    var dev=r[0], mac=r[1], rssi=r[2];
	    if (byMac[mac] == undefined) {
		aboutIp[mac] = {'mac' : mac, 'dev' : dev, 'rssi' : rssi};
	    } else {
		byMac[mac]['dev'] = dev;
		byMac[mac]['rssi'] = rssi;
	    }
	});

	function str(t, suff) {
	    return (t == undefined) ? '' : 
		(t + ((suff == undefined) ? '' : (' ' + suff)));
	}
	function nameCell(name, mac) {
	    if (name && name != "*") {
		return name;
	    }
	    return knownMacAddr[mac] ? knownMacAddr[mac] : "";
	}

	$(target).html('<table><tr> <th class="name">Name</th> <th class="lease">Lease</th> <th class="ip">IP address</th> <th class="rssi">dBm</th> <th class="mac">MAC address</th> </tr></table>');
	var table = $(target).find('table');

	$.each(aboutIp, function (ip, rest) {
	    if (ignoreIpAddr(ip)) {
		return;
	    }

	    $('<tr><td>'+nameCell(rest['name'], rest['mac'])+
	      '</td><td class="lease">'+str((rest['lease'] || "").replace("0 days, ", ""))+
	      '</td><td class="ip">'+str(ip)+
	      '</td><td class="rssi">'+str(rest['rssi'])+
              '</td><td class="mac">'+str(rest['mac'])+
	      '</td></tr>').appendTo(table).addClass(rest['rssi'] ? "signal" : "nosignal");
	});
	$(window).trigger("relayout");
    }

    $.getScript(tomatoUrl[0], 
		function (data, textStatus) { renderTomato(data, "#wifi1") });
    $.getScript(tomatoUrl[1], 
		function (data, textStatus) { renderTomato(data, "#wifi2") });

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
				 "system.noaa.ksql.temp_f"],
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