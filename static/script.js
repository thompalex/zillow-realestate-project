
let map;
let markers = [];
let count = 0;

function initMap() {
    // create the JS map
    map = new google.maps.Map(document.getElementById("map"), {
        center: { lat: 38.94641509233513, lng: -101.5581748813782 },
        zoom: 4,
    });
}

window.initMap = initMap;

// Ensure that we retain selected values in dropdowns
document.getElementsByName("dropDownItem").forEach(item => item.addEventListener('click', (e) => {
    // console.log(e.target.parentNode.parentNode.children[0].textContent);
    e.currentTarget.parentNode.parentNode.children[0].textContent = e.target.text;
}));

// Used to add a delay in code
function delay(time) {
    return new Promise(resolve => setTimeout(resolve, time));
}

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
    // If we have already run a query, our animations need to be adjusted
    if (count > 0) {
        document.getElementById('title1').classList.remove('tableFadeIn');
        document.getElementById('title2').classList.remove('tableFadeIn');
        document.getElementById('table').classList.remove('tableFadeIn');
        document.getElementById('table2').classList.remove('tableFadeIn');
        document.getElementById('loader').style.height = "120px";
    }
    count += 1;
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
        for (i = 0; i < data.length; i++) {
            // For each row, we need to update the table and add markers
            var current_row = document.getElementById('r' + (i + 1).toString());
            var current_elements = current_row.children;
            current_elements[1].innerHTML = data[i]['Neighborhood'];
            current_elements[2].innerHTML = data[i]['City'];
            current_elements[3].innerHTML = data[i]['State'];
            current_elements[4].innerHTML = data[i]['Price'];
            current_elements[5].innerHTML = data[i]['monthly_payment'];
            // The following code creates a new google maps marker and adds it to the map
            var latlon = data[i]['latlon']
            if (latlon != "") {
                var latlon_split = latlon.split(',')
                var maps_latlng = { lat: +(latlon_split[0]), lng: +(latlon_split[1]) }
                var marker = new google.maps.Marker({
                    position: maps_latlng,
                    map: map,
                    title: data[i]['Neighborhood'],
                });
                markers.push(marker)
            }
        }
        // This code fades the tables and titles into view after removing the loader
        document.getElementById('loader').style.opacity = 0;
        document.getElementById('loader').style.height = 0;
        document.getElementById('table').classList.add('tableFadeIn');
        document.getElementById('table2').classList.add('tableFadeIn');
        document.getElementById('title1').classList.add('tableFadeIn');
        document.getElementById('title2').classList.add('tableFadeIn');
    })
})
