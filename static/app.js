// Chart module
const ChartModule = {
    fetchDefaultChart: function(showDesignZone) {
        return fetch(`/api/default-chart?showDesignZone=${showDesignZone}`)
            .then(function(response) {
                if (!response.ok) throw new Error(response.statusText);
                return response.json();
            })
            .then(function(data) {
                return data.figure;
            });
    },

    generateChart: function(file, showDesignZone) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('showDesignZone', showDesignZone);
        return fetch('/api/generate-chart', {
            method: 'POST',
            body: formData
        })
        .then(function(response) {
            if (!response.ok) throw new Error(response.statusText);
            return response.json();
        })
        .then(function(data) {
            return data.figure;
        });
    },

    plotManualPoint: function(temperature, humidity, showDesignZone) {
        const formData = new FormData();
        formData.append('temperature', temperature);
        formData.append('humidity', humidity);
        formData.append('showDesignZone', showDesignZone);
        return fetch('/api/plot-point', {
            method: 'POST',
            body: formData
        })
        .then(function(response) {
            if (!response.ok) throw new Error(response.statusText);
            return response.json();
        })
        .then(function(data) {
            return data.figure;
        });
    },

    clearChart: function() {
        return fetch('/api/clear-data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
        .then(function(response) {
            if (!response.ok) throw new Error(response.statusText);
            return response.json();
        })
        .then(function(data) {
            return data.figure;
        });
    },

    renderChart: function(container, figure) {
        const fig = JSON.parse(figure);
        Plotly.newPlot(container, fig.data, fig.layout);
    }
};

// UI module
const UIModule = {
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
            ChartModule.fetchDefaultChart(designZoneCheckbox.checked)
                .then(function(figure) {
                    ChartModule.renderChart(chartContainer, figure);
                    statusMessage.textContent = '';
                })
                .catch(function(error) {
                    statusMessage.textContent = 'Error updating design zone: ' + error.message;
                    console.error('Error:', error);
                });
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
            const temperature = parseFloat(tempInput.value);
            const humidity = parseFloat(humidityInput.value);
            if (isNaN(temperature) || isNaN(humidity)) {
                manualInputStatus.textContent = 'Please enter valid numbers!';
                return;
            }
            manualInputStatus.textContent = 'Plotting point...';
            ChartModule.plotManualPoint(temperature, humidity, designZoneCheckbox.checked)
                .then(function(figure) {
                    ChartModule.renderChart(chartContainer, figure);
                    manualInputStatus.textContent = '';
                })
                .catch(function(error) {
                    manualInputStatus.textContent = 'Error plotting point: ' + error.message;
                    console.error('Error:', error);
                });
        });
    }
};

// Initialize the app
document.addEventListener('DOMContentLoaded', function() {
    UIModule.init();
});
