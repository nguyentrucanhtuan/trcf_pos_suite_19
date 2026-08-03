// geo_attendance.js
// Geolocation attendance check-in/check-out logic
// Module: trcf_fnb_staff
// GPS polling: every 5 seconds using setInterval

(function () {
    'use strict';

    // ===== CONSTANTS =====
    const GPS_INTERVAL_MS = 5000;
    const GPS_OPTIONS = { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 };
    const LOW_ACCURACY_THRESHOLD = 5; // metres — suspicious if lower

    // ===== STATE =====
    let geoInterval = null;
    let geoLocations = []; // Loaded from template context
    let currentStatus = 'idle'; // idle | checked_in | done

    // ===== INIT =====

    /**
     * Initialise the Geo Attendance module.
     * Called once the DOM is ready and the tab "Chấm Công" is visible.
     * @param {Array<{id, name, lat, lon, radius}>} locations - Active geo locations from server
     * @param {string} initialStatus - 'idle' | 'checked_in' | 'done'
     */
    function init(locations, initialStatus) {
        geoLocations = locations || [];
        currentStatus = initialStatus || 'idle';
        updateUI();

        if (!navigator.geolocation) {
            showGpsUnsupported();
            return;
        }

        startGeoWatch();

        // Pause when tab hidden, resume when visible (saves battery on mobile)
        document.addEventListener('visibilitychange', function () {
            if (document.hidden) {
                stopGeoWatch();
            } else {
                startGeoWatch();
            }
        });
    }

    // ===== GPS POLLING =====

    /**
     * Start GPS polling: get position immediately, then every GPS_INTERVAL_MS ms.
     */
    function startGeoWatch() {
        updatePosition();
        if (!geoInterval) {
            geoInterval = setInterval(updatePosition, GPS_INTERVAL_MS);
        }
    }

    /**
     * Stop GPS polling.
     */
    function stopGeoWatch() {
        if (geoInterval) {
            clearInterval(geoInterval);
            geoInterval = null;
        }
    }

    /**
     * Request current GPS position and update UI.
     */
    function updatePosition() {
        navigator.geolocation.getCurrentPosition(
            onPositionSuccess,
            onPositionError,
            GPS_OPTIONS
        );
    }

    /**
     * Called when browser returns a GPS position.
     * @param {GeolocationPosition} pos
     */
    function onPositionSuccess(pos) {
        const lat = pos.coords.latitude;
        const lon = pos.coords.longitude;
        const accuracy = pos.coords.accuracy;

        const match = findClosestLocation(lat, lon);

        if (match) {
            const dist = haversineDistance(lat, lon, match.lat, match.lon);
            const inRange = dist <= match.radius;
            renderGpsStatus(inRange, dist, match.name, accuracy);
            setCheckinButtonEnabled(inRange && currentStatus === 'idle');
            setCheckoutButtonEnabled(inRange && currentStatus === 'checked_in');
        } else {
            renderGpsStatus(false, null, null, accuracy);
            setCheckinButtonEnabled(false);
            setCheckoutButtonEnabled(false);
        }

        // Warn if accuracy suspiciously low (possible GPS spoofing)
        const warningEl = document.getElementById('geo-accuracy-warning');
        if (warningEl) {
            warningEl.style.display = accuracy < LOW_ACCURACY_THRESHOLD ? 'block' : 'none';
        }
    }

    /**
     * Called when GPS fails.
     * @param {GeolocationPositionError} err
     */
    function onPositionError(err) {
        const i18n = window.TRCF_STAFF_I18N || {};
        let msg = i18n.gps_error_default || 'Unable to determine GPS location.';
        if (err.code === err.PERMISSION_DENIED) {
            msg = i18n.gps_error_permission_denied || msg;
        } else if (err.code === err.POSITION_UNAVAILABLE) {
            msg = i18n.gps_error_unavailable || msg;
        } else if (err.code === err.TIMEOUT) {
            msg = i18n.gps_error_timeout || msg;
        }
        showGpsError(msg);
    }

    // ===== GEOFENCE MATH =====

    /**
     * Haversine formula — returns distance in metres between two GPS coordinates.
     * @param {number} lat1
     * @param {number} lon1
     * @param {number} lat2
     * @param {number} lon2
     * @returns {number} distance in metres
     */
    function haversineDistance(lat1, lon1, lat2, lon2) {
        const R = 6371000; // Earth radius in metres
        const phi1 = (lat1 * Math.PI) / 180;
        const phi2 = (lat2 * Math.PI) / 180;
        const dPhi = ((lat2 - lat1) * Math.PI) / 180;
        const dLambda = ((lon2 - lon1) * Math.PI) / 180;
        const a =
            Math.sin(dPhi / 2) * Math.sin(dPhi / 2) +
            Math.cos(phi1) * Math.cos(phi2) * Math.sin(dLambda / 2) * Math.sin(dLambda / 2);
        return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    }

    /**
     * Find the closest configured geo location to current position.
     * Returns the location object if any location matches (distance <= radius),
     * otherwise returns the absolute closest (for distance display).
     * @param {number} lat
     * @param {number} lon
     * @returns {{id, name, lat, lon, radius, dist}|null}
     */
    function findClosestLocation(lat, lon) {
        if (!geoLocations.length) return null;
        let closest = null;
        let minDist = Infinity;
        geoLocations.forEach(function (loc) {
            const dist = haversineDistance(lat, lon, loc.lat, loc.lon);
            if (dist < minDist) {
                minDist = dist;
                closest = Object.assign({}, loc, { dist: dist });
            }
        });
        return closest;
    }

    // ===== CHECK-IN / CHECK-OUT ACTIONS =====

    /**
     * Perform check-in via AJAX.
     * Called when employee clicks the Check-in button.
     */
    function doCheckIn() {
        navigator.geolocation.getCurrentPosition(function (pos) {
            const payload = {
                lat: pos.coords.latitude,
                lon: pos.coords.longitude,
                accuracy: pos.coords.accuracy,
            };
            setCheckinButtonEnabled(false);
            callJsonRpc('/dang-ky-ca/geo-checkin', payload)
                .then(function (result) {
                    if (result.success) {
                        currentStatus = 'checked_in';
                        updateUI();
                        const i18n = window.TRCF_STAFF_I18N || {};
                        const msg = (i18n.checkin_success || 'Checked in successfully at {time} at {location}')
                            .replace('{time}', result.check_in).replace('{location}', result.location_name);
                        showToast(msg, 'success');
                        if (result.ip_suspicious) {
                            showToast(i18n.ip_suspicious_warning || 'Warning: device not on office WiFi.', 'warning');
                        }
                    } else {
                        handleCheckError(result.error, result);
                        setCheckinButtonEnabled(true);
                    }
                })
                .catch(function () {
                    showToast((window.TRCF_STAFF_I18N || {}).connection_error || 'Connection error. Please try again.', 'error');
                    setCheckinButtonEnabled(true);
                });
        }, onPositionError, GPS_OPTIONS);
    }

    /**
     * Perform check-out via AJAX.
     * Called when employee clicks the Check-out button.
     */
    function doCheckOut() {
        navigator.geolocation.getCurrentPosition(function (pos) {
            const payload = {
                lat: pos.coords.latitude,
                lon: pos.coords.longitude,
                accuracy: pos.coords.accuracy,
            };
            setCheckoutButtonEnabled(false);
            callJsonRpc('/dang-ky-ca/geo-checkout', payload)
                .then(function (result) {
                    if (result.success) {
                        currentStatus = 'done';
                        updateUI();
                        const i18n = window.TRCF_STAFF_I18N || {};
                        const msg = (i18n.checkout_success || 'Checked out successfully! Total hours worked: {hours}')
                            .replace('{hours}', result.worked_hours_display);
                        showToast(msg, 'success');
                        renderDoneSummary(result);
                    } else {
                        handleCheckError(result.error, result);
                        setCheckoutButtonEnabled(true);
                    }
                })
                .catch(function () {
                    showToast((window.TRCF_STAFF_I18N || {}).connection_error || 'Connection error. Please try again.', 'error');
                    setCheckoutButtonEnabled(true);
                });
        }, onPositionError, GPS_OPTIONS);
    }

    /**
     * Handle error codes returned from the server.
     * @param {string} errorCode
     * @param {Object} result - Full result object from server
     */
    function handleCheckError(errorCode, result) {
        const i18n = window.TRCF_STAFF_I18N || {};
        const messages = {
            out_of_range: (i18n.error_out_of_range || 'Out of range. Distance: {distance}m (radius: {radius}m)')
                .replace('{distance}', result.distance_m || '?').replace('{radius}', result.radius_m || '?'),
            ip_blocked: i18n.error_ip_blocked || 'Device is not connected to the office WiFi network.',
            already_checked_in: (i18n.error_already_checked_in || 'Already checked in at {time}. Please check out first.')
                .replace('{time}', result.check_in || ''),
            no_open_session: i18n.error_no_open_session || 'No open work session. Please check in first.',
            no_location_configured: i18n.error_no_location_configured || 'Location has no GPS configuration. Please contact admin.',
            no_employee: i18n.error_no_employee || 'Employee information not found. Please contact HR.',
        };
        const msg = messages[errorCode] || i18n.error_default || 'An error occurred. Please try again.';
        showToast(msg, 'error');
    }

    // ===== UI RENDERING =====

    /**
     * Update overall UI based on currentStatus.
     */
    function updateUI() {
        const idlePanel = document.getElementById('geo-idle-panel');
        const checkedInPanel = document.getElementById('geo-checked-in-panel');
        const donePanel = document.getElementById('geo-done-panel');

        if (idlePanel) idlePanel.style.display = currentStatus === 'idle' ? 'block' : 'none';
        if (checkedInPanel) checkedInPanel.style.display = currentStatus === 'checked_in' ? 'block' : 'none';
        if (donePanel) donePanel.style.display = currentStatus === 'done' ? 'block' : 'none';
    }

    /**
     * Render GPS status text and badge.
     * @param {boolean} inRange
     * @param {number|null} dist - Distance in metres
     * @param {string|null} locationName
     * @param {number} accuracy - GPS accuracy in metres
     */
    function renderGpsStatus(inRange, dist, locationName, accuracy) {
        const badge = document.getElementById('geo-status-badge');
        const distText = document.getElementById('geo-distance-text');
        const locName = document.getElementById('geo-location-name');

        const i18n = window.TRCF_STAFF_I18N || {};
        if (badge) {
            badge.className = 'geo-status-badge ' + (inRange ? 'valid' : 'invalid');
            badge.innerHTML = inRange
                ? '<i class="fa fa-map-marker"></i> ' + (i18n.gps_valid || 'Valid ✓')
                : '<i class="fa fa-map-marker"></i> ' + (i18n.gps_invalid || 'Out of range ✗');
        }
        if (distText && dist !== null) {
            distText.textContent = dist < 1000
                ? Math.round(dist) + ' ' + (i18n.meters_from_nearest || 'meters from nearest location')
                : (dist / 1000).toFixed(1) + ' ' + (i18n.km_from_nearest || 'km from nearest location');
        }
        if (locName && locationName) {
            locName.textContent = locationName;
        }
    }

    /**
     * Render the done summary panel after checkout.
     * @param {Object} result - Server checkout result
     */
    function renderDoneSummary(result) {
        const hoursEl = document.getElementById('geo-done-hours');
        const salaryEl = document.getElementById('geo-done-salary');
        if (hoursEl) hoursEl.textContent = result.worked_hours_display || '–';
        if (salaryEl) salaryEl.textContent = result.salary_display ? result.salary_display + ' đ' : '–';
    }

    function setCheckinButtonEnabled(enabled) {
        const btn = document.getElementById('geo-checkin-btn');
        if (btn) btn.disabled = !enabled;
    }

    function setCheckoutButtonEnabled(enabled) {
        const btn = document.getElementById('geo-checkout-btn');
        if (btn) btn.disabled = !enabled;
    }

    function showGpsUnsupported() {
        const el = document.getElementById('geo-unsupported-msg');
        if (el) el.style.display = 'block';
        stopGeoWatch();
    }

    function showGpsError(msg) {
        const el = document.getElementById('geo-error-msg');
        if (el) { el.textContent = msg; el.style.display = 'block'; }
        setCheckinButtonEnabled(false);
        setCheckoutButtonEnabled(false);
    }

    /**
     * Show a toast notification.
     * @param {string} msg
     * @param {'success'|'warning'|'error'} type
     */
    function showToast(msg, type) {
        // Use Odoo's built-in notification if available
        if (window.odoo && window.odoo.define) {
            // OWL environment — use service notification if accessible
        }
        // Fallback: simple DOM toast
        const container = document.getElementById('geo-toast-container');
        if (!container) return;
        const toast = document.createElement('div');
        const colors = { success: '#28a745', warning: '#ffc107', error: '#dc3545' };
        toast.style.cssText = 'padding:12px 18px;margin-bottom:8px;border-radius:6px;color:white;font-size:0.9rem;background:' + (colors[type] || '#333');
        toast.textContent = msg;
        container.appendChild(toast);
        setTimeout(function () { if (toast.parentNode) toast.parentNode.removeChild(toast); }, 4000);
    }

    // ===== AJAX HELPER =====

    /**
     * Call Odoo JSON-RPC endpoint.
     * @param {string} route
     * @param {Object} params
     * @returns {Promise<Object>}
     */
    function callJsonRpc(route, params) {
        return fetch(route, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params: params }),
        })
            .then(function (res) { return res.json(); })
            .then(function (data) {
                if (data.error) throw data.error;
                return data.result;
            });
    }

    // ===== PUBLIC API =====
    window.GeoAttendance = { init: init, doCheckIn: doCheckIn, doCheckOut: doCheckOut };
})();
