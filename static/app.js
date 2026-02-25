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
        Plotly.newPlot(container, fig.data, fig.layout, {responsive: true});
    }
};

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

    handleChartUpdate: function(promise, statusEl) {
        var chartContainer = document.getElementById('chartContainer');
        return promise
            .then(function(figure) {
                ChartModule.renderChart(chartContainer, figure);
                statusEl.textContent = '';
            })
            .catch(function(error) {
                statusEl.textContent = 'Error: ' + error.message;
                console.error('Error:', error);
            });
    },

    init: function() {
        const fileInput = document.getElementById('fileInput');
        const designZoneCheckbox = document.getElementById('designZone');
        const designZoneInputs = document.getElementById('designZoneInputs');
        const statusMessage = document.getElementById('statusMessage');
        const chartContainer = document.getElementById('chartContainer');
        const tempInput = document.getElementById('tempInput');
        const humidityInput = document.getElementById('humidityInput');
        const plotPointButton = document.getElementById('plotPointButton');
        const manualInputStatus = document.getElementById('manualInputStatus');
        const updateChartFromFileButton = document.getElementById('updateChartFromFileButton');
        const clearDataButton = document.getElementById('clearDataButton');

        // Load default chart on page load
        ChartModule.fetchDefaultChart(false)
            .then(function(figure) {
                ChartModule.renderChart(chartContainer, figure);
            })
            .catch(function(error) {
                statusMessage.textContent = 'Error loading default chart: ' + error.message;
                console.error('Error:', error);
            });

        // Handle design zone checkbox change
        designZoneCheckbox.addEventListener('change', function() {
            designZoneInputs.style.display = designZoneCheckbox.checked ? 'block' : 'none';
            if (designZoneCheckbox.checked) {
                var params = getDesignZoneParams();
                if (!params.valid) {
                    statusMessage.textContent = params.error;
                    return;
                }
                statusMessage.textContent = 'Updating design zone...';
                UIModule.handleChartUpdate(ChartModule.fetchDefaultChart(true, params), statusMessage);
            } else {
                statusMessage.textContent = 'Updating design zone...';
                UIModule.handleChartUpdate(ChartModule.fetchDefaultChart(false), statusMessage);
            }
        });

        // Auto-update chart when zone inputs change
        function handleZoneInputChange() {
            if (!designZoneCheckbox.checked) return;
            var params = getDesignZoneParams();
            if (!params.valid) {
                statusMessage.textContent = params.error;
                return;
            }
            statusMessage.textContent = 'Updating design zone...';
            UIModule.handleChartUpdate(ChartModule.fetchDefaultChart(true, params), statusMessage);
        }

        ['zoneMinTemp', 'zoneMaxTemp', 'zoneMinRH', 'zoneMaxRH'].forEach(function(id) {
            document.getElementById(id).addEventListener('change', handleZoneInputChange);
        });

        // Handle file upload via button click
        updateChartFromFileButton.addEventListener('click', function(event) {
            event.preventDefault();
            if (!fileInput.files[0]) {
                statusMessage.textContent = 'Please select a file!';
                return;
            }
            var zoneParams = null;
            if (designZoneCheckbox.checked) {
                var params = getDesignZoneParams();
                if (!params.valid) {
                    statusMessage.textContent = params.error;
                    return;
                }
                zoneParams = params;
            }
            statusMessage.textContent = 'Updating chart...';
            ChartModule.generateChart(fileInput.files[0], designZoneCheckbox.checked, zoneParams)
                .then(function(figure) {
                    ChartModule.renderChart(chartContainer, figure);
                    statusMessage.textContent = '';
                    fileInput.value = '';
                })
                .catch(function(error) {
                    statusMessage.textContent = 'Error updating chart: ' + error.message;
                    console.error('Error:', error);
                });
        });

        // Handle clear data button click
        clearDataButton.addEventListener('click', function(event) {
            event.preventDefault();
            statusMessage.textContent = 'Clearing data...';
            ChartModule.clearChart()
                .then(function(figure) {
                    ChartModule.renderChart(chartContainer, figure);
                    statusMessage.textContent = 'Data cleared successfully.';
                })
                .catch(function(error) {
                    statusMessage.textContent = 'Error clearing data: ' + error.message;
                    console.error('Error:', error);
                });
        });

        // Handle manual input
        plotPointButton.addEventListener('click', function() {
            if (UIModule.isLoading) return;
            const temperature = parseFloat(tempInput.value);
            const humidity = parseFloat(humidityInput.value);
            if (isNaN(temperature) || isNaN(humidity)) {
                manualInputStatus.textContent = 'Please enter valid numbers!';
                return;
            }
            if (temperature < -10 || temperature > 50) {
                manualInputStatus.textContent = 'Temperature must be between -10°C and 50°C.';
                return;
            }
            var zoneParams = null;
            if (designZoneCheckbox.checked) {
                var params = getDesignZoneParams();
                if (!params.valid) {
                    manualInputStatus.textContent = params.error;
                    return;
                }
                zoneParams = params;
            }
            UIModule.isLoading = true;
            manualInputStatus.textContent = 'Plotting point...';
            UIModule.handleChartUpdate(
                ChartModule.plotManualPoint(temperature, humidity, designZoneCheckbox.checked, zoneParams),
                manualInputStatus
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
