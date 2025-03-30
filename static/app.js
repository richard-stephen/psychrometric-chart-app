// Chart module
const ChartModule = {
    fetchDefaultChart: function(showDesignZone) {
        return fetch(`http://localhost:8000/api/default-chart?showDesignZone=${showDesignZone}`)
            .then(function(response) {
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
        return fetch('http://localhost:8000/api/generate-chart', {
            method: 'POST',
            body: formData
        })
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            return data.figure;
        });
    },

    renderChart: function(container, figure) {
        Plotly.newPlot(container, JSON.parse(figure).data, JSON.parse(figure).layout);
    }
};

// UI module
const UIModule = {
    init: function() {
        const chartForm = document.getElementById('uploadForm');
        const fileInput = document.getElementById('fileInput');
        const designZoneCheckbox = document.getElementById('designZone');
        const statusMessage = document.getElementById('statusMessage');
        const chartContainer = document.getElementById('chartContainer');

        // Load default chart on page load
        ChartModule.fetchDefaultChart(false)
            .then(function(figure) {
                ChartModule.renderChart(chartContainer, figure);
            })
            .catch(function(error) {
                statusMessage.textContent = 'Error loading default chart: ' + error.message;
                console.error('Error:', error);
            });

        // Handle file upload
        chartForm.addEventListener('submit', function(event) {
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
    }
};

// Initialize the app
document.addEventListener('DOMContentLoaded', function() {
    UIModule.init();
});