function main_map_init (map, options) {
    map.on('click', function(e) {        
        var popLocation= e.latlng;
        var coord = e.latlng;
        var lat = coord.lat;
        var lon = coord.lng;
        console.log("You clicked the map at latitude: " + lat + " and longitude: " + lon);
        var url = encodeURI('http://127.0.0.1:8001/api/v2/query?registry=group&key=elevation_group'+'&x='+lon+'&y='+lat)
        var oReq = new XMLHttpRequest();
        oReq.onload = reqListener;
        oReq.open("GET", url)
        oReq.send();
    });
    function reqListener () {
        console.log(this.responseText);
      }
}