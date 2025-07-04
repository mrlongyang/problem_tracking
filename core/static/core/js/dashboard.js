const chartData = JSON.parse(document.getElementById('chart-data').textContent);

new Chart(document.getElementById("statusChart"), {
     type: "doughnut",
     data: {
          labels: chartData.status.labels,
          datasets: [{
               data: chartData.status.data,
               backgroundColor: ['#28a745', '#ffc107', '#dc3545', '#007bff', '#6c757d']
          }]
     }
});

new Chart(document.getElementById("priorityChart"), {
     type: "bar",
     data: {
          labels: chartData.priority.labels,
          datasets: [{
               label: 'Issue Count',
               data: chartData.priority.data,
               backgroundColor: ['#a3e635', '#facc15', '#ef4444', '#0d6efd']
          }]
     }
});