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


function makeChart(container, raceId, numRacers) {
  var chart = new google.visualization.Timeline(container);
  var dataTable = new google.visualization.DataTable();
  dataTable.addColumn({ type: 'string', id: 'Name' });
  dataTable.addColumn({ type: 'string', id: 'whatever' });
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
      var url = GOOGLE_REV_GEOCODE_URL+"?latlng="+latlng+"&key="+api_key;
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
      timeline: {singleColor: '#8d8'},
      tooltip: {isHtml: true}
    };
    $('.google-visualization-tooltip').remove();
    google.visualization.events.addListener(chart, 'onmouseover', handleMouseover);
    chart.draw(dataTable, options);
    // done, remove progress bar
    if (numFetched == numRacers) {
      $('#progress').hide();
    }
  };

  return {
    showBreaks: function(racerName) {
      /*
       * given name of the racer fetch break data from the server
       */
      $.getJSON("/breaks/"+raceId+"?name="+racerName, function(feed) { 
        feed.breaks.forEach(function(brk) {
          var start = new Date(brk.start),
              end = new Date(brk.end);
          var loc = brk.lat+", "+brk.lng;
          // there's only one spot/break for any racer at a given location
          // so the pair of racer name and a location should be unique,
          // giving a valid id for a break
          var breakId = racerName.replace(" ", "-")+"*"+brk.lat+","+brk.lng;
          var tooltip = createToolTip(brk, loc, breakId);
          breakCache[breakId] = brk;
          dataTable.addRow([racerName, "", tooltip, start, end]);
        });

        updateChart();
      }); 
    },
  };
}

function plot(raceId) {
  $.getJSON("/racers/"+raceId, function(feed) {
    var container = document.getElementById('breaks-timeline');
    var chart = makeChart(container, raceId, feed.racers.length);
    feed.racers.forEach(function(racer) {
      chart.showBreaks(racer);
    });
  });
}

function main() {
  plot(raceId);
}
