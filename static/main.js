google.setOnLoadCallback(main);


function makeChart(container, raceId, numRacers) {
  var chart = new google.visualization.Timeline(container);
  var dataTable = new google.visualization.DataTable();
  dataTable.addColumn({ type: 'string', id: 'Name' });
  dataTable.addColumn({ type: 'string', id: 'whatever' });
  dataTable.addColumn({ type: 'string', role: "tooltip" });
  dataTable.addColumn({ type: 'date', id: 'Start' });
  dataTable.addColumn({ type: 'date', id: 'End' });
  var fetched = 0;

  return {
    showBreaks: function(racerName) {
      /*
       * given name of the racer fetch break data from the server
       */
      $.getJSON("/breaks/"+raceId+"?name="+racerName, function(feed) {
        feed.breaks.forEach(function(brk) {
          var tooltip = "Druation: "+brk.duration;
          dataTable.addRow([racerName, "", tooltip, new Date(brk.start), new Date(brk.end)]);
        });

        fetched += 1;
        // update progress bar
        var percentDone = (fetched/numRacers*100).toFixed(2)+"%";
        var visualProgress = "Loading data - "+percentDone;
        $('#progress-display').text(visualProgress);
        $('#progress-bar').width(percentDone);

        // add data to chart
        var options = {
          // magic
          height: numRacers * 50 + 30,
          timeline: {singleColor: '#8d8'}
        };
        $('.google-visualization-tooltip').remove();
        chart.draw(dataTable, options);

        // done, remove progress bar
        if (fetched == numRacers) {
          $('#progress').hide();
        }
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
