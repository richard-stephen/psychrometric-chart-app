// Chart module
const ChartModule = {
    fetchAndParse: function(url, options) {
        return fetch(url, options)
            .then(function(response) {
                if (!response.ok) throw new Error(response.statusText);
                return response.json();
            })
            .then(function(data) {
                return data.figure;
            });
    },

    fetchDefaultChart: function(showDesignZone, zoneParams) {
        var url = `/api/default-chart?showDesignZone=${showDesignZone}`;
        if (showDesignZone && zoneParams) {
            url += `&minTemp=${zoneParams.minTemp}&maxTemp=${zoneParams.maxTemp}&minRH=${zoneParams.minRH}&maxRH=${zoneParams.maxRH}`;
        }
        return ChartModule.fetchAndParse(url);
    },

    generateChart: function(file, showDesignZone, zoneParams) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('showDesignZone', showDesignZone);
        if (showDesignZone && zoneParams) {
            formData.append('minTemp', zoneParams.minTemp);
            formData.append('maxTemp', zoneParams.maxTemp);
            formData.append('minRH', zoneParams.minRH);
            formData.append('maxRH', zoneParams.maxRH);
        }
        return ChartModule.fetchAndParse('/api/generate-chart', { method: 'POST', body: formData });
    },

    plotManualPoint: function(temperature, humidity, showDesignZone, zoneParams) {
        const formData = new FormData();
        formData.append('temperature', temperature);
        formData.append('humidity', humidity);
        formData.append('showDesignZone', showDesignZone);
        if (showDesignZone && zoneParams) {
            formData.append('minTemp', zoneParams.minTemp);
            formData.append('maxTemp', zoneParams.maxTemp);
            formData.append('minRH', zoneParams.minRH);
            formData.append('maxRH', zoneParams.maxRH);
        }
        return ChartModule.fetchAndParse('/api/plot-point', { method: 'POST', body: formData });
    },

    clearChart: function() {
        return ChartModule.fetchAndParse('/api/clear-data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
    },

    renderChart: function(container, figure) {
        const fig = JSON.parse(figure);
        Plotly.newPlot(container, fig.data, fig.layout);
    }
};

var storedZoneParams = { minTemp: 20, maxTemp: 24, minRH: 40, maxRH: 60 };
var currentFile = null;
var currentManualPoint = null;

function refreshChart(showZone, zoneParams) {
    if (currentFile) {
        return ChartModule.generateChart(currentFile, showZone, zoneParams);
    }
    if (currentManualPoint) {
        return ChartModule.plotManualPoint(
            currentManualPoint.temperature,
            currentManualPoint.humidity,
            showZone,
            zoneParams
        );
    }
    return ChartModule.fetchDefaultChart(showZone, zoneParams);
}

function showToast(message, type) {
    var container = document.getElementById('toastContainer');
    var ariaLive = document.getElementById('statusMessage');
    var toast = document.createElement('div');
    toast.className = 'toast' + (type === 'success' ? ' success' : '');
    toast.textContent = message;

    if (ariaLive) {
        ariaLive.textContent = message;
    }

    function dismiss() {
        toast.classList.add('fade-out');
        setTimeout(function() {
            if (toast.parentNode) toast.parentNode.removeChild(toast);
        }, 400);
    }

    toast.addEventListener('click', dismiss);
    container.appendChild(toast);
    setTimeout(dismiss, 4000);
}

function getDesignZoneParams() {
    var minTemp = parseFloat(document.getElementById('zoneMinTemp').value);
    var maxTemp = parseFloat(document.getElementById('zoneMaxTemp').value);
    var minRH   = parseFloat(document.getElementById('zoneMinRH').value);
    var maxRH   = parseFloat(document.getElementById('zoneMaxRH').value);

    if (isNaN(minTemp) || isNaN(maxTemp) || isNaN(minRH) || isNaN(maxRH)) {
        return { valid: false, error: 'Please enter valid numbers for all design zone fields.' };
    }
    if (minTemp >= maxTemp) {
        return { valid: false, error: 'Minimum temperature must be less than maximum temperature.' };
    }
    if (minTemp < -10 || maxTemp > 50) {
        return { valid: false, error: 'Design zone temperatures must be between -10°C and 50°C.' };
    }
    if (minRH >= maxRH) {
        return { valid: false, error: 'Minimum RH must be less than maximum RH.' };
    }
    if (minRH < 0 || maxRH > 100) {
        return { valid: false, error: 'Design zone RH values must be between 0% and 100%.' };
    }
    return { valid: true, minTemp: minTemp, maxTemp: maxTemp, minRH: minRH, maxRH: maxRH };
}

// UI module
const UIModule = {
    isLoading: false,

    handleChartUpdate: function(promise) {
        var chartContainer = document.getElementById('chartContainer');
        return promise
            .then(function(figure) {
                ChartModule.renderChart(chartContainer, figure);
            })
            .catch(function(error) {
                showToast('Error: ' + error.message, 'error');
                console.error('Error:', error);
            });
    },

    init: function() {
        const fileInput = document.getElementById('fileInput');
        const designZoneCheckbox = document.getElementById('designZone');
        const configureButton = document.getElementById('configureZoneButton');
        const designZoneModal = document.getElementById('designZoneModal');
        const applyButton = document.getElementById('applyZoneButton');
        const cancelButton = document.getElementById('cancelZoneButton');
        const chartContainer = document.getElementById('chartContainer');
        const tempInput = document.getElementById('tempInput');
        const humidityInput = document.getElementById('humidityInput');
        const plotPointButton = document.getElementById('plotPointButton');
        const updateChartFromFileButton = document.getElementById('updateChartFromFileButton');
        const clearDataButton = document.getElementById('clearDataButton');

        var zoneWasActive = false;

        function openZoneModal(wasActive) {
            zoneWasActive = wasActive;
            document.getElementById('zoneMinTemp').value = storedZoneParams.minTemp;
            document.getElementById('zoneMaxTemp').value = storedZoneParams.maxTemp;
            document.getElementById('zoneMinRH').value = storedZoneParams.minRH;
            document.getElementById('zoneMaxRH').value = storedZoneParams.maxRH;
            designZoneModal.showModal();
        }

        // Load default chart on page load
        ChartModule.fetchDefaultChart(false)
            .then(function(figure) {
                ChartModule.renderChart(chartContainer, figure);
            })
            .catch(function(error) {
                showToast('Error loading default chart: ' + error.message, 'error');
                console.error('Error:', error);
            });

        // Handle design zone checkbox change
        designZoneCheckbox.addEventListener('change', function() {
            if (designZoneCheckbox.checked) {
                openZoneModal(false);
            } else {
                configureButton.style.display = 'none';
                UIModule.handleChartUpdate(refreshChart(false, null));
            }
        });

        // Configure button reopens modal when zone is already active
        configureButton.addEventListener('click', function() {
            openZoneModal(true);
        });

        // Modal Apply button
        applyButton.addEventListener('click', function() {
            var params = getDesignZoneParams();
            if (!params.valid) {
                showToast(params.error, 'error');
                return;
            }
            storedZoneParams = { minTemp: params.minTemp, maxTemp: params.maxTemp, minRH: params.minRH, maxRH: params.maxRH };
            designZoneModal.close();
            configureButton.style.display = 'inline';
            UIModule.handleChartUpdate(refreshChart(true, storedZoneParams));
        });

        // Modal Cancel button
        cancelButton.addEventListener('click', function() {
            designZoneModal.close();
            if (!zoneWasActive) {
                designZoneCheckbox.checked = false;
                configureButton.style.display = 'none';
            }
        });

        // Escape key closes modal (cancel event)
        designZoneModal.addEventListener('cancel', function() {
            if (!zoneWasActive) {
                designZoneCheckbox.checked = false;
                configureButton.style.display = 'none';
            }
        });

        // Handle file upload via button click
        updateChartFromFileButton.addEventListener('click', function(event) {
            event.preventDefault();
            if (!fileInput.files[0]) {
                showToast('Please select a file!', 'error');
                return;
            }
            var theFile = fileInput.files[0];
            var zoneParams = designZoneCheckbox.checked ? storedZoneParams : null;
            ChartModule.generateChart(theFile, designZoneCheckbox.checked, zoneParams)
                .then(function(figure) {
                    currentFile = theFile;
                    currentManualPoint = null;
                    ChartModule.renderChart(chartContainer, figure);
                    fileInput.value = '';
                })
                .catch(function(error) {
                    showToast('Error updating chart: ' + error.message, 'error');
                    console.error('Error:', error);
                });
        });

        // Handle clear data button click
        clearDataButton.addEventListener('click', function(event) {
            event.preventDefault();
            UIModule.handleChartUpdate(ChartModule.clearChart().then(function(figure) {
                currentFile = null;
                currentManualPoint = null;
                return figure;
            }));
        });

        // Handle manual input
        plotPointButton.addEventListener('click', function() {
            if (UIModule.isLoading) return;
            const temperature = parseFloat(tempInput.value);
            const humidity = parseFloat(humidityInput.value);
            if (isNaN(temperature) || isNaN(humidity)) {
                showToast('Please enter valid numbers!', 'error');
                return;
            }
            if (temperature < -10 || temperature > 50) {
                showToast('Temperature must be between -10°C and 50°C.', 'error');
                return;
            }
            var zoneParams = designZoneCheckbox.checked ? storedZoneParams : null;
            UIModule.isLoading = true;
            UIModule.handleChartUpdate(
                ChartModule.plotManualPoint(temperature, humidity, designZoneCheckbox.checked, zoneParams)
                    .then(function(figure) {
                        currentManualPoint = { temperature: temperature, humidity: humidity };
                        currentFile = null;
                        return figure;
                    })
            ).finally(function() {
                UIModule.isLoading = false;
            });
        });
    }
};

// Initialize the app
document.addEventListener('DOMContentLoaded', function() {
    UIModule.init();
});
