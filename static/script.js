let chart = new Chart(document.getElementById("phChart"), {
    type: 'line',
    data: {
      labels: [],
      datasets: [{
        label: 'pH Value',
        data: [],
        borderColor: '#0078d7',
        fill: false
      }]
    }
  });
  
  function start() {
    document.getElementById("system-status").textContent = "Collecting data...";
    // simulate data
    setInterval(() => {
      let ph = (Math.random() * 14).toFixed(2);
      document.getElementById("ph-value").textContent = ph;
      chart.data.labels.push(new Date().toLocaleTimeString());
      chart.data.datasets[0].data.push(ph);
      chart.update();
    }, 2000);
  }
  
  function stop() {
    document.getElementById("system-status").textContent = "Stopped";
  }
  