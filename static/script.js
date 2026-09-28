let tempChart;

async function loadChartData() {
  const response = await fetch("/data");
  const sensorData = await response.json();

  const ctx = document.getElementById("myChart").getContext("2d");

  tempChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: sensorData.labels,
      datasets: [{
        label: 'Temperature (°C)',
        data: sensorData.values,
        borderColor: '#0078d7',
        backgroundColor: 'rgba(0,120,215,0.1)',
        fill: true,
        tension: 0.3
      }]
    }, 
     options: {
     responsive: true,
      plugins: {
        legend: { position: 'top' },
        title: { display: true, text: 'Temperature Trend' }
      },
      scales: {
        y: {
          min: -10,
          max: 50,
          title: { display: true, text: '°C' }
        }
      }
    }
  });
} 
setInterval(loadChartData, 1000);

loadChartData();


async function refreshData() {
  const response = await fetch('/data');
  const sensorData = await response.json();

  tempChart.data.labels.push(sensorData.time);
  tempChart.data.datasets[0].data.push(sensorData.temperature);

  tempChart.update();
}

/*
async function refreshData() {
  try {
    const response = await fetch('/data');   // Flask API
    const sensorData = await response.json();

    const newValue = sensorData.temperature; // ან sensorData.values.slice(-1)[0]

    tempChart.data.labels.push(new Date().toLocaleTimeString());
    tempChart.data.datasets[0].data.push(newValue);

    tempChart.update();
    console.log("New data added:", newValue);
  } catch (error) {
    console.error("Error refreshing data:", error);
  }
}

*/

  
function openSettings() {
  document.getElementById("settingsModal").style.display = "block";
}

function closeSettings() {
  document.getElementById("settingsModal").style.display = "none";
}

function saveSettings() {
  const interval = document.getElementById("refreshInterval").value;
  alert("Saved refresh interval: " + interval + " seconds");
  closeSettings();
}


  
  async function viewLogs() {
    const response = await fetch('/log', { method: 'POST' });
    const result = await response.json();
    alert("Logs saved: " + result.status);
  }
  
  function exportData() {
    window.location.href = "/export";
  }
  