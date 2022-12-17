
let map;
let markers = [];
let resultDisplay = false;
let errorDisplay = false;

function initMap() {
    // create the JS map
    map = new google.maps.Map(document.getElementById("map"), {
        center: { lat: 38.94641509233513, lng: -101.5581748813782 },
        zoom: 4,
    });
}

// Ensure that we retain selected values in dropdowns
document.getElementsByName("dropDownItem").forEach(item => item.addEventListener('click', (e) => {
    // console.log(e.target.parentNode.parentNode.children[0].textContent);
    e.currentTarget.parentNode.parentNode.children[0].textContent = e.target.text;
}));

// Used to add a delay in code
function delay(time) {
    return new Promise(resolve => setTimeout(resolve, time));
}


function addLocation(latlon, title, infowindow, bounds) {

    if (latlon != "") {
        var latlon_split = latlon.split(',')
        var maps_latlng = { lat: +(latlon_split[0]), lng: +(latlon_split[1]) }
        var marker = new google.maps.Marker({
            position: maps_latlng,
            map: map,
            title: title,
        });

        bounds.extend(marker.getPosition());
        google.maps.event.addListener(marker, 'click', (function (marker, i) {
            return function () {
                infowindow.setContent(marker.getTitle());
                infowindow.open(map, marker);
                map.setZoom(12);
                map.setCenter(marker.getPosition());
            }
        })(marker, i));

        google.maps.event.addListener(marker, 'dblclick', (function (marker, i) {
            return function () {
                map.setZoom(30);
                map.setCenter(marker.getPosition());
            }
        })(marker, i));

        markers.push(marker)
    }
    map.fitBounds(bounds);
}

window.initMap = initMap;

// This is where we actually query and process results, changing the HTML as needed
document.getElementById('getResults').addEventListener('click', async (e) => {
    // Remove all current markers from the map
    while (markers.length > 0) {
        var curr = markers.pop()
        curr.setMap(null);
        curr = null;
    }
    // Get all of the dropdown menus and load their results into a dictionary
    var dropdowns = document.getElementsByClassName('dropdown');
    var d = {};
    for (i = 0; i < dropdowns.length; i++) {
        d[dropdowns[i].children[0].name] = dropdowns[i].children[0].textContent;
    }
    if (errorDisplay) {
        document.getElementById('titlelog').classList.remove('tableFadeIn');
        const errorlog = document.getElementById('errorlog');
        errorlog.classList.remove('tableFadeIn');
        errorlog.innerHTML = '';
        document.getElementById('loader').style.height = "120px";
        errorDisplay = false;
    }
    // If we have already run a query, our animations need to be adjusted
    if (resultDisplay) {
        document.getElementById('table2').getElementsByClassName('table')[0].innerHTML = ''
        document.getElementById('table').getElementsByClassName('table')[0].innerHTML = ''
        document.getElementById('title1').classList.remove('tableFadeIn');
        document.getElementById('title2').classList.remove('tableFadeIn');
        document.getElementById('table').classList.remove('tableFadeIn');
        document.getElementById('table2').classList.remove('tableFadeIn');
        document.getElementById('loader').style.height = "120px";
        resultDisplay = false
    }
    if (d['forecast'] == "True") {
        document.getElementById('title1').innerHTML = "Highest Price Changes";
        document.getElementById('title2').innerHTML = "Lowest Price Changes";
    } else {
        document.getElementById('title1').innerHTML = "Most Expensive";
        document.getElementById('title2').innerHTML = "Least Expensive";
    }
    // animate the row to extend and then add the loader in
    document.getElementById('tablerow').classList.add('tableRowAnimate');
    await delay(1000)
    document.getElementById('loader').style.opacity = 1;
    // Fetch results from the backend, sending the dict of options the user selected
    fetch('/api', {
        method: "POST",
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(d)
    }
    ).then(res => res.json()).then(data => {
        // Once we have recieved the results, we must process it
        console.log(data)
        if (data['tables'] && data['dfs']){
            var infowindow = new google.maps.InfoWindow();
            var bounds = new google.maps.LatLngBounds();
            if (data['dfs'][0].length > 0){
                var top_five = data['dfs'][0];
                document.getElementById('table').innerHTML = data['tables'][0];
                for (i=0; i < top_five.length; i++){
                    latlon = top_five[i]['latlon'];
                    title = top_five[i]['Neighborhood'];
                    if (latlon != 0){
                        addLocation(latlon, title, infowindow, bounds);
                    }
                }
                document.getElementById('table').classList.add('tableFadeIn');
                document.getElementById('title1').classList.add('tableFadeIn');
                resultDisplay = true;
            } else {
                var log = document.getElementById('errorlog');
                const field = document.createElement('li');
                field.innerHTML = 'Cannot find any expensive places';
                log.appendChild(field);
                document.getElementById('titlelog').classList.add('tableFadeIn');
                document.getElementById('errorlog').classList.add('tableFadeIn');
                errorDisplay = true;
            }
            if (data['dfs'][1].length > 0){
                var bottom_five = data['dfs'][1];
                document.getElementById('table2').innerHTML = data['tables'][1];
                for (i=0; i < bottom_five.length; i++){
                    latlon = bottom_five[i]['latlon'];
                    title = bottom_five[i]['Neighborhood'];
                    if (latlon != 0){
                        addLocation(latlon, title, infowindow, bounds);
                    }
                }
                document.getElementById('title2').classList.add('tableFadeIn');
                document.getElementById('table2').classList.add('tableFadeIn');
            } else {
                var log = document.getElementById('errorlog');
                const field = document.createElement('li');
                field.innerHTML = 'Cannot find any cheap places';
                log.appendChild(field);
                document.getElementById('titlelog').classList.add('tableFadeIn');
                document.getElementById('errorlog').classList.add('tableFadeIn');
                errorDisplay = true;
            }
        } else {
            var log = document.getElementById('errorlog');
        
            for (var error in data) {
                const field = document.createElement('li');
                field.innerHTML = data[error];
                log.appendChild(field);
            }
            
            document.getElementById('loader').style.opacity = 0;
            document.getElementById('loader').style.height = 0;
            document.getElementById('titlelog').classList.add('tableFadeIn');
            document.getElementById('errorlog').classList.add('tableFadeIn');
    
            errorDisplay = true;
        }
        // This code fades the tables and titles into view after removing the loader
        document.getElementById('loader').style.opacity = 0;
        document.getElementById('loader').style.height = 0;
    })
})
