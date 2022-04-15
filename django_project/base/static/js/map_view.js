// Globals
var marker = false;
var startFetchTime = 0;
var currentTab = ''; // Contains str of current registry (service, group, collection)
let outputText = true;

// Listen to map click
window.addEventListener("map:init", function (e) {
    var detail = e.detail;
    window.map = detail.map;
    detail.map.on('click', function(e) {        
        let coord = e.latlng;
        let lat = coord.lat;
        let lon = coord.lng;
        if (currentTab.length != 0) {
            let key = document.getElementById(currentTab + "-select").value;
            let token = document.getElementById(currentTab + "-token").value;
            fetch(currentTab, key, lat, lon, token);
        }
    });

    // Dynamically create HTML for sidebar panels 
    let registries = {'service': services, 'group': groups, 'collection': collections};
    let html = {};
    for (const registry in registries) {
        let timer = '<div id="' + registry + '-timer"></div>';
        let lat= '<label>Latitude: </label><input class=input-field type="number" step=0.0001 id="' + registry + '-lat-box" value="0.0000"/>';
        let lng = '<label>Longitude: </label><input class=input-field type="number" step=0.0001 id="' + registry + '-lon-box" value="0.0000"/>';
        let token = '<label>Token: </label><input class=input-field type="text" id="' + registry + '-token" value=""/>';
        let button = '<button class="fetch-button" type="button" id=' + registry + '-button>Fetch</button>';
        let options = '<label> '+ registry.charAt(0).toUpperCase() + registry.slice(1) + 's: </label><select class="select-dropdown" name="' + registry + '" id="' + registry + '-select">';
        registries[registry].forEach(function (value) {
            if (registry == 'service' && value.key=='altitude'){
                options += '<option value='+ value.key + ' selected>' + value.name + '</option>';
            }
            options += '<option value='+ value.key + '>' + value.name + '</option>';
        })
        options += '</select></div>';
        let table = '<div class="result-table" id="' + registry + '-table"></div>';
        let url = '<div class="url-query" id="' + registry + '-url" style="margin-top: 15px;"></div>';
        let output = '<div class="output" id="' + registry + '-output" style="display: none">' +
            '<button class="output-text" disabled id="' + registry + '-text">Text</button>' +
            '<button class="output-chart" id="' + registry + '-chart">Chart</button></div>';
        html[registry] = lat + lng + token + button + options + output + timer + table + url;
    };
    // create the sidebar instance and add it to the map
    L.control.sidebar({ container: 'sidebar' })
    .addTo(detail.map)
    .addPanel({
            id: 'service',
            tab: '<i class="fa fa-square-o"></i>',
            title: 'Services',
            pane: html['service']
        }).addPanel({
            id: 'group',
            tab: '<i class="fa fa-object-ungroup"></i>',
            title: 'Groups',
            pane: html['group']
        }).addPanel({
            id: 'collection',
            tab: '<i class="fa fa-object-group"></i>',
            title: 'Collections',
            pane: html['collection']
        })
    .on('content', function(e) {
        currentTab = e.id;
    })
    .open('service');
    // Load styles
    var styles = document.createElement('link');
    styles.href = 'css/map_view.css';
    document.getElementsByTagName('head')[0].appendChild(styles);

},false);
// Listen for sidebar Fetch button 
document.addEventListener('click',function(e) {

    if (currentTab.length != 0) {
        document.getElementById(currentTab + "-select").onchange = function (){
            document.getElementById(currentTab + "-output").style.display= "none";
        }
        if (e.target && e.target.id== currentTab + "-button" || e.target.id== currentTab + "-text") {
            var lat = document.getElementById(currentTab + "-lat-box").value;
            var lon = document.getElementById(currentTab + "-lon-box").value;
            var key = document.getElementById(currentTab + "-select").value;
            var token = document.getElementById(currentTab + "-token").value;
            outputText = true;
            fetch(currentTab, key, lat, lon, token);
        }
        if (e.target && e.target.id== currentTab + "-chart") {
            var lat = document.getElementById(currentTab + "-lat-box").value;
            var lon = document.getElementById(currentTab + "-lon-box").value;
            var key = document.getElementById(currentTab + "-select").value;
            var token = document.getElementById(currentTab + "-token").value;
            outputText = false;
            document.getElementById(currentTab + "-text").disabled = false;
            fetch(currentTab, key, lat, lon, token);
        }

    }

});


// Functions
function fetch (registry, key, lat, lon, token){
    // We update all coord boxes on all tabs
    updateCoordBoxes(lat, lon);
    // We remove existing markers
    if (marker) {marker.remove()};
    marker = L.marker([lat, lon]).addTo(window.map);
    let baseUrl = window.location.origin;
    let url = encodeURI(baseUrl + '/api/v2/query?registry='+registry+'&key='+key+'&x='+lon+'&y='+lat+'&token='+token+'&outformat=json');
    let urlEl = document.getElementById(currentTab + "-url");
    urlEl.innerHTML = '<h5>Geocontext API query</h5>' + url;
    document.getElementById(currentTab + "-table").innerHTML = '<div class="loader"></div>'
    startFetchTime = (new Date()).getTime();
    let request = new XMLHttpRequest();
    request.onload = requestListener;
    request.open("GET", url)
    request.send();
}
function updateCoordBoxes(lat, lon) {
    document.getElementById("service-lat-box").value = parseFloat(lat).toFixed(6);
    document.getElementById("service-lon-box").value = parseFloat(lon).toFixed(6);
    document.getElementById("group-lat-box").value = parseFloat(lat).toFixed(6);
    document.getElementById("group-lon-box").value = parseFloat(lon).toFixed(6);
    document.getElementById("collection-lat-box").value = parseFloat(lat).toFixed(6);
    document.getElementById("collection-lon-box").value = parseFloat(lon).toFixed(6);
}
function requestListener () {
    let endFetchTime = (new Date()).getTime();
    let endTime = endFetchTime - startFetchTime;
    let timeEl = document.getElementById(currentTab + "-timer");
    timeEl.style.margin = "15px 0 0 0";
    timeEl.innerHTML = '<h5>Results</H5> Request time:  ' + endTime + 'ms';
    let data = JSON.parse(this.responseText);
    buildTable(data);
    if(outputText){
            buildTable(data);
    }
    else{
        buildChart(data)
    }
 }

 function buildInfoTable(data){
    let info_table = `<table border='1'><caption style="caption-side:top">`+ currentTab.charAt(0).toUpperCase() + currentTab.slice(1) + ` details</caption>`;
    for (row in data) {
        if (row != 'groups' && row != 'services' && row != 'group_type') {

            info_table += "<tr><td class='first-column'>" + row + "</td><td>" + roundAny(data[row]) + "</td></tr>";
        }
    }
    info_table += "</table>"
     return info_table
 };

 function buildTable (data) {
     let data_table = ''
    let info_table = buildInfoTable(data);
    if ('groups' in data) {
        data['groups'].sort().forEach(function (group) {
            if(group['group_type'] == 'graph'){
                document.getElementById(currentTab + "-output").style.display= "block";
            }
            new_table = `<table border='1'><caption style="caption-side:top">` + group['name'] + ` group service values</caption>`;
            group['services'].sort().forEach(function (service) {
                new_table += "<tr><td class='first-column'>" + service['name'] + "</td><td>" + roundAny(service['value']) + "</td></tr>";
            });
            new_table += "</table>";
            data_table += new_table;
        });
    } else if ('services' in data) {
        if(data['group_type'] == 'graph'){
            document.getElementById(currentTab + "-output").style.display= "block";
        }
        data_table += `<table border='1'><caption style="caption-side:top">Service values</caption>`;
        data['services'].sort().forEach(function (service) {
            data_table += "<tr><td class='first-column'>" + service['name'] + "</td><td>" + roundAny(service['value']) + "</td></tr>";
        });
        data_table += "</table>";
    }
    document.getElementById(currentTab + "-table").innerHTML = info_table + data_table;
};
function roundAny (value) {
    // Round value if number - else ignore
    if (!Number.isNaN(parseFloat(value))) {
        value = parseFloat(value).toFixed(2)
    }
    return value
}

function buildChart(data){
    let chart_container = ''
    let info_table = buildInfoTable(data);
    let chart_data = [];
    let chart_id = '';
    let chart_name = '';
    let chart_categories = []
    if ('groups' in data) {

        data['groups'].sort().forEach(function (group, index, array) {
            chart_id = group['key'];
            chart_name = data['name'];
            var chart_collection_data = {};
            chart_collection_data['data'] = [];
            chart_collection_data['name'] = group['name'];

            if(group['group_type'] == 'graph') {
                chart_container = `<table border='1'><caption style="caption-side:top">` + data['name'] + ` Chart</caption> <tr style='border: none' id=`+chart_id+`></tr>`;
                group['services'].sort().forEach(function (service) {
                    chart_collection_data['data'].push(parseFloat(roundAny(service['value'])));
                    let split = service['key'].split("_")
                    chart_categories.push(split[split.length -1].substring(0,3).replace(/(^\w|\s\w)/g, m => m.toUpperCase()));
                });
                chart_data.push(chart_collection_data);
            }

            chart_container += "</table>";
        });

    } else if ('services' in data) {
        chart_id = data['key'];
        chart_name = data['name'];
        chart_container += `<table border='1'><caption style="caption-side:top">Service chart</caption>`;
        chart_container += "<tr style='border: none' id="+chart_id+"></tr>";
        var chart_group_data = {};
        chart_group_data['data'] = [];
        chart_group_data['name'] = data['name'];

        data['services'].sort().forEach(function (service) {
           chart_group_data['data'].push(parseFloat(roundAny(service['value'])));
           let split = service['key'].split("_")
           chart_categories.push(split[split.length -1].substring(0,3).replace(/(^\w|\s\w)/g, m => m.toUpperCase()));
        });
        chart_data.push(chart_group_data);
        chart_container += "</table>";

    }
    document.getElementById(currentTab + "-table").innerHTML = info_table + chart_container;
    console.log(chart_data)

    Highcharts.chart(chart_id, {
        chart: {
                type: 'spline'
            },
            title: {
                text: chart_name
            },
            xAxis: {
                categories: chart_categories,
                tickInterval: 3
            },
            yAxis: {
                title: {
                    text: chart_name
                }
            },
            plotOptions: {
                line: {
                    dataLabels: {
                        enabled: true
                    },
                    enableMouseTracking: false
                }
            },
             legend: {
                layout: 'horizontal',
                enabled: true,
                verticalAlign: 'top'
            },
            exporting: {
                buttons: {
                    contextButton: {
                        menuItems: ["printChart",
                            "separator",
                            "downloadPNG",
                            "downloadJPEG",
                            "downloadPDF",
                            "downloadSVG",
                            "separator",
                            "downloadCSV",
                            "downloadXLS"]
                    }
                }
            },
            series: chart_data
    });
}