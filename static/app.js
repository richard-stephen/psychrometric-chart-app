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

    fetchDefaultChart: function(showDesignZone) {
        return ChartModule.fetchAndParse(`/api/default-chart?showDesignZone=${showDesignZone}`);
    },

    generateChart: function(file, showDesignZone) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('showDesignZone', showDesignZone);
        return ChartModule.fetchAndParse('/api/generate-chart', { method: 'POST', body: formData });
    },

    plotManualPoint: function(temperature, humidity, showDesignZone) {
        const formData = new FormData();
        formData.append('temperature', temperature);
        formData.append('humidity', humidity);
        formData.append('showDesignZone', showDesignZone);
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
            statusMessage.textContent = 'Updating design zone...';
            UIModule.handleChartUpdate(
                ChartModule.fetchDefaultChart(designZoneCheckbox.checked),
                statusMessage
            );
        });

        // Handle file upload via button click
        updateChartFromFileButton.addEventListener('click', function(event) {
            event.preventDefault();
            if (!fileInput.files[0]) {
                statusMessage.textContent = 'Please select a file!';
                return;
            }
            statusMessage.textContent = 'Updating chart...';
            ChartModule.generateChart(fileInput.files[0], designZoneCheckbox.checked)
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
            UIModule.isLoading = true;
            manualInputStatus.textContent = 'Plotting point...';
            UIModule.handleChartUpdate(
                ChartModule.plotManualPoint(temperature, humidity, designZoneCheckbox.checked),
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
