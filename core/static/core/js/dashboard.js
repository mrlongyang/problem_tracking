document.addEventListener('DOMContentLoaded', function () {
  const chartData = JSON.parse(document.getElementById('chart-data').textContent);

  // Status Chart
  const statusCtx = document.getElementById('statusChart').getContext('2d');
  new Chart(statusCtx, {
    type: 'pie',
    data: {
      labels: chartData.status.labels,
      datasets: [{
        data: chartData.status.data,
        backgroundColor: ['#007bff', '#28a745', '#dc3545', '#ffc107', '#17a2b8']
      }]
    },
    options: {
      plugins: {
        legend: { display: true, position: 'bottom' },
        title: { display: true, text: 'Problem Status Breakdown', font: { size: 16 } }
      }
    }
  });

  // Priority Chart
  const priorityCtx = document.getElementById('priorityChart').getContext('2d');
  new Chart(priorityCtx, {
    type: 'bar',
    data: {
      labels: chartData.priority.labels,
      datasets: [{
        label: 'Number of Problems',
        data: chartData.priority.data,
        backgroundColor: ['#dc3545', '#ffc107', '#28a745']
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: true, position: 'top' },
        title: { display: true, text: 'Problems by Priority', font: { size: 16 } }
      },
      scales: {
        y: { beginAtZero: true, ticks: { stepSize: 1 } }
      }
    }
  });

  // Monthly Trend Chart
  const monthlyCtx = document.getElementById('monthlyChart').getContext('2d');
  new Chart(monthlyCtx, {
    type: 'line',
    data: {
      labels: chartData.monthly.labels,
      datasets: [{
        label: 'Problems Created',
        data: chartData.monthly.data,
        fill: false,
        borderColor: '#007bff',
        tension: 0.3,
        pointBackgroundColor: '#007bff',
        pointBorderWidth: 1,
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: true, position: 'top' },
        title: { display: true, text: 'Monthly Problem Trends', font: { size: 16 } }
      },
      scales: {
        y: { beginAtZero: true, ticks: { stepSize: 1 } }
      }
    }
  });
});
