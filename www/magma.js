
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
	})
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

});