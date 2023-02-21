const barChart = document.getElementById("barChart");
const pieChart = document.getElementById("pieChart");
const areaChart = document.getElementById("areaChart");

// Setup

if (view == 'date'){
    labelSize = 24
} else if (view == 'month') {
    labelSize = 30
} else if (view == 'year') {
    labelSize = 12
}

labels = Array.from({ length: labelSize }, (_, i) => i + 1);

sum_visits = new Array(labelSize).fill(0);
sum_leaves = new Array(labelSize).fill(0);
delta_visits = new Array(labelSize).fill(0);
delta_visits_colors = new Array(labelSize).fill(0);
visit_hour = new Array(labelSize).fill(0);
visit_pollen_hour = new Array(labelSize).fill(0);
visit_share = [0, 0];

// Preparation

timestamps.forEach(function (value, index) {
  if (view == 'date'){
  label_index = new Date(value).getHours() - 1;
  } else if (view == 'month') {
  label_index = new Date(value).getDate() - 1;
  } else if (view == 'year') {
  label_index = new Date(value).getMonth();
  }

  // bar data
  delta_visits[label_index] += visit[index] + visit_pollen[index] - leave[index] - leave_pollen[index];

  if (delta_visits[label_index]  > 0) {
    delta_visits_colors[label_index] = '#C5D4EB'
  } else {
    delta_visits_colors[label_index] = '#003777'
  }
  // bar data 2
  sum_visits[label_index] += visit[index] + visit_pollen[index];
  sum_leaves[label_index] += leave[index] + leave_pollen[index];
  // pie data
  visit_share[0] += visit_pollen[index];
  visit_share[1] += visit[index];
  // area data
  visit_hour[label_index] += visit[index];
  visit_pollen_hour[label_index] += visit_pollen[index];
});

// Data

bar_difference_hour = {
  labels: labels,
  datasets: [
    {
      label: "Čebele",
      data: delta_visits,
      borderWidth: 1,
      borderColor: delta_visits_colors,
      backgroundColor: delta_visits_colors,
    },
  ],
};

bar_visit_leave = {
  labels: labels,
  datasets: [
    {
      label: "Prihod",
      data: sum_visits,
      borderWidth: 1,
      borderColor: "#C5D4EB",
      backgroundColor: "#C5D4EB",
    },
    {
      label: "Odhod",
      data: sum_leaves,
      borderWidth: 1,
      borderColor: "#003777",
      backgroundColor: "#003777",
    },
  ],
};

pie_visit_share = {
  labels: ["Cvetni prah", "Brez"],
  datasets: [
    {
      label: "Delež prihoda",
      data: visit_share,
      backgroundColor: ["#DECB21", "#992409"],
      hoverOffset: 4,
    },
  ],
};

area_pollen_hour = {
  labels: labels,
  datasets: [{
    label: 'Brez',
    data: visit_hour,
    fill: 'origin',
    borderColor: '#992409',
    backgroundColor: '#992409',
    tension: 0.1
  },{
    label: 'Cvetni prah',
    data: visit_pollen_hour,
    fill: 'stack',
    borderColor: '#DECB21',
    backgroundColor: '#DECB21',
    tension: 0.1
  }]
};

// Configuration

let barConfig = {
  type: "bar",
  data: bar_visit_leave,
  options: {
    responsive: true,
    interaction: {
      mode: "index",
      intersect: false,
    },
    stacked: false,
    plugins: {
      title: {
        display: true,
        text: "Štetje",
      },
    },
    scales: {
      y: {
        type: "linear",
        display: true,
        position: "left",
      },
    },
  },
};

let pieConfig = {
  type: "pie",
  data: pie_visit_share,
  options: {
    responsive: true,
    interaction: {
      mode: "index",
      intersect: false,
    },
    stacked: false,
    plugins: {
      title: {
        display: true,
        text: "Delež cvetnega praha",
      },
    },
  },
};

let areaConfig = {
  type: "line",
  data: area_pollen_hour,
  options: {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: "index",
      intersect: false,
    },
    stacked: true,
    plugins: {
      title: {
        display: true,
        text: "Prihod",
      },
    },
    scales: {
      y: {
        stacked: true
      }
    }
  },
};

bar = new Chart(barChart, barConfig);
pie = new Chart(pieChart, pieConfig);
area = new Chart(areaChart, areaConfig);

function difference() {
  barConfig["data"] = bar_difference_hour;
  bar.update();
}

function total() {
  barConfig["data"] = bar_visit_leave;
  bar.update();
}
