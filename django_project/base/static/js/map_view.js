// Globals
var marker = false;
var startFetchTime = 0;
var currentTab = ''; // Contains str of current registry (service, group, collection)

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
            fetch(currentTab, key, lat, lon);
        }
    });
    // Dynamically create HTML for sidebar panels 
    let registries = {'service': services, 'group': groups, 'collection': collections};
    let html = {};
    for (const registry in registries) {
        let timer = '<div id="' + registry + '-timer"></div>';
        let lat= '<label>Latitude: </label><input class=input-field type="number" step=0.0001 id="' + registry + '-lat-box" value="0.0000"/>';
        let lng = '<label>Longitude: </label><input class=input-field type="number" step=0.0001 id="' + registry + '-lon-box" value="0.0000"/>';
        let button = '<button class="fetch-button" type="button" id=' + registry + '-button>Fetch</button>';
        let options = '<label> '+ registry.charAt(0).toUpperCase() + registry.slice(1) + 's: </label><select class="select-dropdown" name="' + registry + '" id="' + registry + '-select">';
        registries[registry].forEach(function (value) {
            options += '<option value='+ value.key + '>' + value.name + '</option>';
        })
        options += '</select></div>';
        let table = '<div class="result-table" id="' + registry + '-table"></div>';
        let url = '<div class="url-query" id="' + registry + '-url"></div>';
        html[registry] = lat + lng + button + options + timer + table + url;
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
        if (e.target && e.target.id== currentTab + "-button") {
            var lat = document.getElementById(currentTab + "-lat-box").value;
            var lon = document.getElementById(currentTab + "-lon-box").value;
            var key = document.getElementById(currentTab + "-select").value;
            fetch(currentTab, key, lat, lon);
        }
    }
});
// Functions
function fetch (registry, key, lat, lon){
    // We update all coord boxes on all tabs
    updateCoordBoxes(lat, lon);
    // We remove existing markers
    if (marker) {marker.remove()};
    marker = L.marker([lat, lon]).addTo(window.map);
    let baseUrl = window.location.origin;
    let url = encodeURI(baseUrl + '/api/v2/query?registry='+registry+'&key='+key+'&x='+lon+'&y='+lat+'&outformat=json');
    let urlEl = document.getElementById(currentTab + "-url");
    urlEl.innerHTML = '<h5>Geocontext API query</H5>' + url;
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
    timeEl.innerHTML = '<h5>Results</H5> Request time:  ' + endTime + 'ms';
    let data = JSON.parse(this.responseText);
    buildTable(data);
 }
 function buildTable (data) {
    let info_table = "<table border='1'><caption>" + currentTab.charAt(0).toUpperCase() + currentTab.slice(1) + " details</caption>";
    let data_table = ''
    for (row in data) {
        if (row != 'groups' && row != 'services') {
            info_table += "<tr><td>" + row + "</td><td>" + roundAny(data[row]) + "</td></tr>";
        }
    }
    info_table += "</table>";
    if ('groups' in data) {
        data['groups'].sort().forEach(function (group) {
            new_table = "<table border='1'><caption>" + group['name'] + " group service values</caption>";
            group['services'].sort().forEach(function (service) {
                new_table += "<tr><td>" + service['name'] + "</td><td>" + roundAny(service['value']) + "</td></tr>";
            });
            new_table += "</table></div>";
            data_table += new_table;
        });
    } else if ('services' in data) {
        sortByMonth(data['services'])
        data_table += "<div><table border='1'><caption>Service values</caption>";
        data['services'].sort().forEach(function (service) {
            data_table += "<tr><td>" + service['name'] + "</td><td>" + roundAny(service['value']) + "</td></tr>";
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

function sortByMonth(services){
    const months = ["january", "february", "march", "april", "may", "june",
        "july", "august", "september", "october", "november", "december"];
    const last = services[0].key.split('_').length - 1
    services.sort(function(a, b){
        return months.indexOf(a.key.split('_')[last])
           > months.indexOf(b.key.split('_')[last]);
    });
}