/** @odoo-module **/
/**
 * Geo Map Picker — Admin backend (trcf.geo.location form view)
 *
 * Features:
 *  - Leaflet.js map with draggable marker + circle
 *  - Click on map to set coordinates
 *  - Address search via Nominatim (OpenStreetMap, free, no API key)
 *  - "Use current location" button (GPS, works only on mobile/devices with GPS)
 *  - Updates Odoo OWL form fields using native input setter + bubbled event
 *  - MutationObserver on documentElement (always non-null at parse time)
 */

(function () {
    "use strict";

    // ── Leaflet loader ────────────────────────────────────────────────────────
    var leafletReady = false;
    var leafletCallbacks = [];

    function onLeafletReady(cb) {
        if (leafletReady) { cb(); return; }
        leafletCallbacks.push(cb);
    }

    function loadLeaflet() {
        if (window.L) {
            leafletReady = true;
            leafletCallbacks.forEach(function (cb) { cb(); });
            return;
        }
        var link = document.createElement("link");
        link.rel = "stylesheet";
        link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
        document.head.appendChild(link);

        var script = document.createElement("script");
        script.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
        script.onload = function () {
            leafletReady = true;
            leafletCallbacks.forEach(function (cb) { cb(); });
        };
        document.head.appendChild(script);
    }

    loadLeaflet();

    // ── Helper: update Odoo OWL field ─────────────────────────────────────────
    // Odoo 17+ wraps each field in <div name="field_name" class="o_field_widget">
    function setFieldValue(fieldName, value) {
        var input = document.querySelector('[name="' + fieldName + '"] input');
        if (!input) return;
        var nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
        nativeSetter.call(input, value);
        input.dispatchEvent(new Event("input", { bubbles: true }));
    }

    function getFieldValue(fieldName) {
        var input = document.querySelector('[name="' + fieldName + '"] input');
        return input ? parseFloat(input.value) || 0 : 0;
    }

    // ── Shared map state ──────────────────────────────────────────────────────
    var mapInstance = null;
    var markerInstance = null;
    var circleInstance = null;

    function moveMap(lat, lon) {
        setFieldValue("latitude", lat.toFixed(7));
        setFieldValue("longitude", lon.toFixed(7));
        if (mapInstance) {
            var latlng = [lat, lon];
            markerInstance.setLatLng(latlng);
            circleInstance.setLatLng(latlng);
        }
    }

    // ── "Dùng vị trí hiện tại" ────────────────────────────────────────────────
    window.geoMapUseCurrentLocation = function () {
        if (!navigator.geolocation) {
            alert("Trình duyệt không hỗ trợ GPS");
            return;
        }
        navigator.geolocation.getCurrentPosition(
            function (pos) {
                var lat = pos.coords.latitude;
                var lon = pos.coords.longitude;
                moveMap(lat, lon);
                if (mapInstance) mapInstance.setView([lat, lon], 18);
            },
            function (err) {
                var msgs = {
                    1: "Bị từ chối quyền GPS. Vào cài đặt trình duyệt → cho phép vị trí cho localhost.",
                    2: "Không xác định được vị trí. Máy tính thường không có GPS — hãy dùng ô Tìm địa chỉ hoặc nhấp trên bản đồ.",
                    3: "Quá thời gian lấy vị trí. Hãy dùng ô Tìm địa chỉ hoặc nhấp trên bản đồ.",
                };
                alert(msgs[err.code] || "Lỗi GPS: " + err.message);
            },
            { enableHighAccuracy: false, timeout: 10000, maximumAge: 60000 }
        );
    };

    // ── Address search via Nominatim ──────────────────────────────────────────
    window.geoMapSearchAddress = function () {
        var input = document.getElementById("geo-address-search");
        if (!input || !input.value.trim()) return;
        var query = input.value.trim();
        var url = "https://nominatim.openstreetmap.org/search?format=json&limit=1&q=" + encodeURIComponent(query);
        fetch(url, { headers: { "Accept-Language": "vi,en" } })
            .then(function (r) { return r.json(); })
            .then(function (results) {
                if (!results || !results.length) {
                    alert("Không tìm thấy địa chỉ: " + query);
                    return;
                }
                var lat = parseFloat(results[0].lat);
                var lon = parseFloat(results[0].lon);
                moveMap(lat, lon);
                if (mapInstance) mapInstance.setView([lat, lon], 17);
            })
            .catch(function () {
                alert("Lỗi kết nối khi tìm địa chỉ. Kiểm tra kết nối Internet.");
            });
    };

    // ── Map initialiser ───────────────────────────────────────────────────────
    function initGeoMap(mapEl) {
        if (mapEl._mapInitialized) return;
        mapEl._mapInitialized = true;

        var initLat = getFieldValue("latitude") || 10.7769;
        var initLon = getFieldValue("longitude") || 106.7009;
        var initRad = getFieldValue("radius") || 100;

        var map = L.map(mapEl).setView([initLat, initLon], 16);
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: "© OpenStreetMap contributors",
            maxZoom: 20,
        }).addTo(map);

        var marker = L.marker([initLat, initLon], { draggable: true }).addTo(map);
        var circle = L.circle([initLat, initLon], { radius: initRad }).addTo(map);

        mapInstance = map;
        markerInstance = marker;
        circleInstance = circle;

        map.on("click", function (e) {
            moveMap(e.latlng.lat, e.latlng.lng);
        });

        marker.on("dragend", function () {
            var pos = marker.getLatLng();
            moveMap(pos.lat, pos.lng);
        });
    }

    // ── Watch for map container ───────────────────────────────────────────────
    function tryInit() {
        var mapEl = document.getElementById("geo-map-picker");
        if (mapEl && !mapEl._mapInitialized) {
            onLeafletReady(function () { initGeoMap(mapEl); });
        }
    }

    // document.documentElement is always non-null at parse time
    var observer = new MutationObserver(tryInit);
    observer.observe(document.documentElement, { childList: true, subtree: true });
    tryInit();
})();
