window.addEventListener("map:init", function (e) {
    var detail = e.detail;
    window.map = detail.map
    detail.map.on('click', function(e) {        
        let coord = e.latlng;
        let lat = coord.lat;
        let lon = coord.lng;
        let service_lat = document.getElementById("service-lat-box")
        service_lat.value = lat.toFixed(6)
        let service_lon = document.getElementById("service-lon-box")
        service_lon.value = lon.toFixed(6)
        fetch(lat, lon)
    });
document.addEventListener('click',function(e){
    if(e.target && e.target.id== 'service-button'){
        let lat = document.getElementById("service-lat-box").value
        let lon = document.getElementById("service-lon-box").value
        fetch(lat, lon)
    }
});
var marker = false
function fetch (lat, lon){
    if (marker) {marker.remove()};
    marker = L.marker([lat, lon]).addTo(window.map);
    let key = document.getElementById("service-select").value
    let registry = "service"
    let baseUrl = window.location.origin;
    let url = encodeURI(baseUrl + '/api/v2/query?registry='+registry+'&key='+key+'&x='+lon+'&y='+lat+'&outformat=json')
    startFetchTime = (new Date()).getTime();
    var request = new XMLHttpRequest();
    request.onload = requestListener;
    request.open("GET", url)
    request.send();
}
function requestListener () {
    let endFetchTime = (new Date()).getTime();
    let endTime = endFetchTime - startFetchTime
    let timeEl = document.getElementById("service-timer");
    timeEl.innerHTML = 'Request time:  ' + endTime + 'ms';
    let resultObj = JSON.parse(this.responseText)
    txt = "<table border='1'>"
    for (x in resultObj) {
        txt += "<tr><td>" + x + "</td><td>" + resultObj[x] + "</td></tr>";
    }
    txt += "</table>"
    document.getElementById("service-table").innerHTML = txt;
    }
// create the sidebar instance and add it to the map
var sidebar = L.control.sidebar({ container: 'sidebar' })
.addTo(detail.map);

// Services tab
let service_timer = '<div id="service-timer"></div>'
let service_lat= '<div id="service-lat"><label>Latitude: </label><input type="number" step=0.0001 id="service-lat-box" value="0.0000" /></div>'
let service_lng = '<div id="service-lng"><label>Longitude: </label><input type="number" step=0.0001 id="service-lon-box" value="0.0000" /></div>'
let service_button = '<div id="service-button-div"><button type="button" id=service-button>Fetch</button></div>'
let service_options = '<div id="service-select-container"><label>Services: </label><select name="services" id="service-select">'
services.forEach(function (service) {
    service_options += '<option value='+ service.key + '>' + service.name + '</option>'
})
service_options += '</select></div>'
let service_table = '<div id="service-table"></div>'
let service_html = service_lat + service_lng + service_button + service_options + service_timer + service_table

// Groups tab
let group_timer = '<div id="service-timer"></div>'
let group_lat= '<div id="group-lat"><label>Latitude: </label><input type="number" step=0.0001 id="group-lat-box" value="0.0000" /></div>'
let group_lng = '<div id="group-lng"><label>Longitude: </label><input type="number" step=0.0001 id="group-lon-box" value="0.0000" /></div>'
let group_options = '<div id="group-select-container"><label>Groups: </label><select name="groups" id="groups-select">'
groups.forEach(function (group) {
    group_options += '<option value='+ group.key + '>' + group.name + '</option>'
})
group_options += '</select></div>'
let group_result = '<div id="service-result"></div>'
let group_html = group_lat + group_lng + group_options + group_timer + group_result

// Collection tab
let collection_timer = '<div id="service-timer"></div>'
let collection_lat= '<div id="collection-lat"><label>Latitude: </label><input type="number" step=0.0001 id="collection-lat-box" value="0.0000" /></div>'
let collection_lng = '<div id="collection-lng"><label>Longitude: </label><input type="number" step=0.0001 id="collection-lon-box" value="0.0000" /></div>'
let collection_options = '<div id="collection-select-container"><label>Collections: </label><select name="collections" id="collection-select">'
collections.forEach(function(collection) {
    collection_options += '<option value='+ collection.key + '>' + collection.name + '</option>'
})
collection_options  += '</select></div>'
let collection_result = '<div id="service-result"></div>'
let collection_html = collection_lat + collection_lng + collection_options + collection_timer + collection_result

// add panels dynamically to the sidebar
sidebar.addPanel({
        id: 'services',
        tab: '<i class="fa fa-square-o"></i>',
        title: 'Services',
        pane: service_html
    }).addPanel({
        id: 'groups',
        tab: '<i class="fa fa-object-ungroup"></i>',
        title: 'Groups',
        pane: group_html
    }).addPanel({
        id: 'collections',
        tab: '<i class="fa fa-object-group"></i>',
        title: 'Collections',
        pane: collection_html
    })
.open('services');
},
false);
