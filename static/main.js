google.setOnLoadCallback(main);

var GOOGLE_REV_GEOCODE_URL = 'https://maps.googleapis.com/maps/api/geocode/json'


function toReadableDate(date) {
  var hours = date.getHours().toString(),
      minutes = date.getMinutes().toString();
  if (minutes.length == 1) {
    minutes = "0"+minutes;
  }
  return date.toDateString()+" at "+hours+":"+minutes;
}


function createToolTip(brk, loc, breakId) {
  var start = new Date(brk.start);
  var tooltipStyle = 'padding:5px 5px 5px 5px; width: 220px; height: 100px;'
    return "<div class='break-display' id='"+breakId+"' style='"+tooltipStyle+"'>"+
    "<b>How long</b>:&nbsp;"+brk.duration+"<br/>"+
    "<b>When</b>:&nbsp;"+toReadableDate(start)+"<br/>"+
    "<b>Where</b>:&nbsp;"+loc+"<br/>"+ 
    "</div>";
}

function makeRacerNameRe(racerName) {
  parts = racerName.split(/\s/);
  reParts = [];
  for (var i = 0; i < parts.length; i++) {
    reParts.push('\\b'+parts[i]);
  }
  return new RegExp(reParts.join('|'), 'i');
} 

function makeChart(container, raceId, numRacers) {
  var matcher;
  var chart = new google.visualization.Timeline(container);
  var dataTable = new google.visualization.DataTable();
  dataTable.addColumn({ type: 'string', id: 'Name' });
  dataTable.addColumn({ type: 'string', id: 'TotalDuration' });
  dataTable.addColumn({ type: 'string', role: 'tooltip', p: {html: true}});
  dataTable.addColumn({ type: 'date', id: 'Start' });
  dataTable.addColumn({ type: 'date', id: 'End' });
  // cache of breaks
  var breakCache = {}
  // cache of addresses (reverse-geocoding result)
  var addrCache = {}
  var numFetched = 0;
  var geocode= function(lat, lng, callback) {
    /*
     * reverse geocode
     */
    var latlng = lat+","+lng;
    // check cache -- avoid unecessary API call
    if (addrCache[latlng] != undefined) {
      var cached = addrCache[latlng];
      var results = cached[0];
      var ok = cached[1];
      callback(results, ok);
    } else {
      var url = GOOGLE_REV_GEOCODE_URL+"?latlng="+latlng;
      return $.getJSON(url, function(resp) {
        var ok = (resp.results != undefined && resp.results.length > 0);
        // save to cache
        addrCache[latlng] = [resp.results, ok];
        callback(resp.results, ok);
        if (!ok) {
          console.error(resp);
        }
      });
    }
  }
  var handleMouseover = function(e) {
    /*
     * deal with mouseover here
     */
    var selected = $('.break-display')[0];
    var breakId = selected.id;
    var brk = breakCache[breakId]; 
    var racerName = breakId.split('*')[0].replace("-", " ");
    var lat = brk.lat,
        lng = brk.lng;
    geocode(lat, lng, function(results, ok) {
      if (ok) {
        var loc = results[0].formatted_address;
        var newToolTip = createToolTip(brk, loc, breakId);
        $(selected).html(newToolTip);
      }
    });
  };

  var updateChart = function() {
    /*
     * closure used to update the chart
     * called when ALL data of a racer are loaded
     * -- including reverse-geocoding data
     */
    numFetched += 1;
    // update progress bar
    var percentDone = (numFetched/numRacers*100).toFixed(2)+"%";
    var visualProgress = "Loading data - "+percentDone;
    $('#progress-display').text(visualProgress);
    $('#progress-bar').width(percentDone);

    // add data to chart
    var options = {
      // magic
      height: numRacers * 50 + 30,
      timeline: {
        singleColor: '#8d8',
        showBarLabels: false
      },
      tooltip: {isHtml: true},
    };
    $('.google-visualization-tooltip').remove();
    google.visualization.events.addListener(chart, 'onmouseover', handleMouseover);
    if (dataTable.getNumberOfRows() == 0) {
      // nothing to show
      $(container).hide();
    } else {
      $(container).show();
      dataTable.sort(1);
      chart.draw(dataTable, options);
    }
    // done, remove progress bar
    if (numFetched == numRacers) {
      $('#progress').hide();
    }
  };

  var addBreak = function(breakId) {
    // only add matched breaks (filter by name)
    var brk = breakCache[breakId];
    if (!matcher || matcher.exec(brk.racerName) !== null) {
      var start = new Date(brk.start);
      var end = new Date(brk.end);
      var loc = brk.lat+", "+brk.lng;
      var tooltip = createToolTip(brk, loc, breakId);
      dataTable.addRow([brk.racerName, brk.totalDuration, tooltip, start, end]);
    }
  };

  var showBreaks = function(racerName) {
    /*
     * given name of the racer fetch break data from the server
     */
    $.getJSON("/breaks/"+raceId+"?name="+racerName, function(feed) { 
      feed.breaks.forEach(function(brk) {
        // TODO remove these two lines to avoid data duplication
        brk.totalDuration=feed.totalDuration;
        brk.racerName = racerName;
        var breakId = racerName.replace(" ", "-")+"*"+brk.lat+","+brk.lng;
        breakCache[breakId] = brk;
        addBreak(breakId);
      }); 
      updateChart();
    }); 
  };

  var filterByName = function(racerName) {
    matcher = racerName === "" ?
      null :
      makeRacerNameRe(racerName);
    console.log('searching with regexp '+matcher);
    dataTable.removeRows(0, dataTable.getNumberOfRows()); 
    for (var breakId in breakCache) { 
      addBreak(breakId);
    }
    updateChart();
  }

  var ext = {
    showBreaks: showBreaks,
    filterByName: filterByName 
  };

  return ext;
}

function plot(raceId) {
  $.getJSON("/racers/"+raceId, function(feed) {
    var container = document.getElementById('breaks-timeline');
    var chart = makeChart(container, raceId, feed.racers.length);
    for (var i = 0; i < feed.racers.length; i++) {
      chart.showBreaks(feed.racers[i]);
    }
    // handle search
    $('#search-input').on('input', function () { 
      var searchedName = $(this).val();
      console.log('Searching '+searchedName);
      chart.filterByName(searchedName.trim());
    });
  });
}

function main() {
  plot(raceId);
}
