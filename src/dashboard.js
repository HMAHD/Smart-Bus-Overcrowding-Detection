// Modern Responsive Smart Bus Dashboard JavaScript
// Enhanced with better animations, mobile support, and alert management

// Global variables
let stopChart = null;
let occupancyChart = null;
let alertQueue = [];
let maxAlerts = 5; // Maximum visible alerts

// Theme Management
function toggleTheme() {
  const body = document.body;
  const currentTheme = body.getAttribute("data-theme");
  const newTheme = currentTheme === "dark" ? "light" : "dark";
  body.setAttribute("data-theme", newTheme);

  const icon = document.getElementById("theme-icon");
  icon.className = newTheme === "dark" ? "fas fa-moon" : "fas fa-sun";

  localStorage.setItem("theme", newTheme);
  updateChartTheme(newTheme);
}

// Mobile Menu Toggle
function toggleMobileMenu() {
  const menu = document.getElementById("mobile-menu");
  menu.classList.toggle("active");
}

// Fullscreen Toggle
function toggleFullscreen() {
  const mapCard = document.querySelector(".map-card");
  if (!document.fullscreenElement) {
    mapCard.requestFullscreen().catch((err) => {
      console.log(`Error attempting to enable fullscreen: ${err.message}`);
    });
  } else {
    document.exitFullscreen();
  }
}

// Clear all alerts
function clearAlerts() {
  const container = document.getElementById("alerts-container");
  const alerts = container.querySelectorAll(".alert-item");

  alerts.forEach((alert, index) => {
    setTimeout(() => {
      alert.classList.add("removing");
      setTimeout(() => alert.remove(), 300);
    }, index * 50);
  });

  setTimeout(() => {
    alertQueue = [];
    updateAlertCount();
  }, alerts.length * 50 + 300);
}

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", () => {
  const savedTheme = localStorage.getItem("theme") || "dark";
  document.body.setAttribute("data-theme", savedTheme);
  document.getElementById("theme-icon").className =
    savedTheme === "dark" ? "fas fa-moon" : "fas fa-sun";

  initializeCharts();
  startRealTimeUpdates();
  initializeAnimations();
  initializeAlerts();

  // Close mobile menu when clicking outside
  document.addEventListener("click", (e) => {
    const menu = document.getElementById("mobile-menu");
    const toggle = document.querySelector(".mobile-menu-toggle");
    if (!menu.contains(e.target) && !toggle.contains(e.target)) {
      menu.classList.remove("active");
    }
  });
});

// Chart configuration
const chartColors = {
  primary: "#3b82f6",
  success: "#10b981",
  warning: "#f59e0b",
  danger: "#ef4444",
  text: "#94a3b8",
  grid: "#2a2a3e",
};

// Initialize Charts with improved responsiveness
function initializeCharts() {
  const stopCtx = document.getElementById("stopChart").getContext("2d");
  stopChart = new Chart(stopCtx, {
    type: "bar",
    data: {
      labels: [
        "Fort",
        "Pettah",
        "Maradana",
        "Borella",
        "Narahenpita",
        "Nugegoda",
      ],
      datasets: [
        {
          label: "Avg Passengers",
          data: [42, 45, 38, 30, 25, 15],
          backgroundColor: (context) => {
            const value = context.parsed.y;
            if (value > 40) return chartColors.danger;
            if (value > 30) return chartColors.warning;
            return chartColors.success;
          },
          borderRadius: 8,
          maxBarThickness: 40,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "rgba(0, 0, 0, 0.9)",
          padding: 12,
          borderRadius: 8,
          titleFont: { size: 12 },
          bodyFont: { size: 11 },
          callbacks: {
            label: (context) =>
              `${context.parsed.y} passengers (${Math.round(
                (context.parsed.y / 50) * 100
              )}%)`,
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 50,
          grid: { color: chartColors.grid, drawBorder: false },
          ticks: {
            color: chartColors.text,
            font: { size: 11 },
          },
        },
        x: {
          grid: { display: false },
          ticks: {
            color: chartColors.text,
            font: { size: 11 },
          },
        },
      },
    },
  });

  const occupancyCtx = document
    .getElementById("occupancyChart")
    .getContext("2d");
  const hours = Array.from({ length: 24 }, (_, i) =>
    i % 3 === 0 ? `${i}:00` : ""
  ); // Show every 3 hours for mobile

  occupancyChart = new Chart(occupancyCtx, {
    type: "line",
    data: {
      labels: hours,
      datasets: [
        {
          label: "Occupancy %",
          data: generateOccupancyData(),
          borderColor: chartColors.primary,
          backgroundColor: "rgba(59, 130, 246, 0.1)",
          borderWidth: 2,
          fill: true,
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 5,
          pointBackgroundColor: chartColors.primary,
          pointBorderColor: "#fff",
          pointBorderWidth: 2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { intersect: false, mode: "index" },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "rgba(0, 0, 0, 0.9)",
          padding: 12,
          borderRadius: 8,
          titleFont: { size: 12 },
          bodyFont: { size: 11 },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          grid: { color: chartColors.grid, drawBorder: false },
          ticks: {
            color: chartColors.text,
            font: { size: 11 },
            callback: (value) => value + "%",
          },
        },
        x: {
          grid: { display: false },
          ticks: {
            color: chartColors.text,
            font: { size: 10 },
            maxRotation: 0,
          },
        },
      },
    },
  });
}

// Generate occupancy data
function generateOccupancyData() {
  const data = [];
  for (let i = 0; i < 24; i++) {
    if (i >= 7 && i <= 9) data.push(80 + Math.random() * 15);
    else if (i >= 17 && i <= 19) data.push(75 + Math.random() * 20);
    else if (i >= 10 && i <= 16) data.push(40 + Math.random() * 30);
    else data.push(10 + Math.random() * 20);
  }
  return data;
}

// Update chart theme
function updateChartTheme(theme) {
  const isDark = theme === "dark";
  chartColors.text = isDark ? "#94a3b8" : "#64748b";
  chartColors.grid = isDark ? "#2a2a3e" : "#e2e8f0";

  [stopChart, occupancyChart].forEach((chart) => {
    if (chart) {
      chart.options.scales.y.grid.color = chartColors.grid;
      chart.options.scales.y.ticks.color = chartColors.text;
      chart.options.scales.x.ticks.color = chartColors.text;
      chart.update();
    }
  });
}

// Fleet bus data
const fleetBuses = [
  {
    id: "BUS-134-CMB",
    status: "normal",
    location: "Borella",
    passengers: 28,
    capacity: 50,
  },
  {
    id: "BUS-142-CMB",
    status: "warning",
    location: "Maradana",
    passengers: 38,
    capacity: 50,
  },
  {
    id: "BUS-156-CMB",
    status: "normal",
    location: "Nugegoda",
    passengers: 12,
    capacity: 50,
  },
  {
    id: "BUS-138-CMB",
    status: "danger",
    location: "Maradana",
    passengers: 50,
    capacity: 50,
  },
];

// Render fleet buses
function renderFleetBuses() {
  const container = document.getElementById("fleet-buses");
  container.innerHTML = "";

  fleetBuses.forEach((bus, index) => {
    const occupancyPercent = Math.round((bus.passengers / bus.capacity) * 100);
    const statusText =
      bus.status === "warning"
        ? "NEARLY FULL"
        : bus.status === "danger"
        ? "OVERCROWDED"
        : "NORMAL";

    const busItem = document.createElement("div");
    busItem.className = "bus-item";
    busItem.style.animationDelay = `${index * 0.05}s`;

    busItem.innerHTML = `
      <div class="bus-item-info">
        <div class="bus-item-id">${bus.id}</div>
        <div class="bus-item-details">
          <span><i class="fas fa-map-marker-alt"></i> ${bus.location}</span>
          <span><i class="fas fa-users"></i> ${bus.passengers}/${bus.capacity}</span>
        </div>
        <div class="progress-bar" style="margin-top: 8px;">
          <div class="progress-fill ${bus.status}" style="width: ${occupancyPercent}%"></div>
        </div>
      </div>
      <span class="bus-item-status ${bus.status}">${statusText}</span>
    `;

    container.appendChild(busItem);
  });
}

// Real-time data simulation
class BusDataSimulator {
  constructor() {
    this.mainBusPassengers = 50; // Start at maximum capacity
    this.direction = -1; // Start by decreasing
    this.currentStop = 2; // Start at Maradana
    this.stops = [
      "Fort",
      "Pettah",
      "Maradana",
      "Borella",
      "Narahenpita",
      "Nugegoda",
    ];
  }

  update() {
    // Simulate more realistic passenger changes
    if (this.mainBusPassengers >= 48) {
      // When overcrowded, more likely to decrease
      this.direction = Math.random() > 0.8 ? 1 : -1;
    } else if (this.mainBusPassengers <= 10) {
      // When nearly empty, more likely to increase
      this.direction = Math.random() > 0.2 ? 1 : -1;
    } else if (Math.random() > 0.9) {
      // Occasionally change direction
      this.direction *= -1;
    }

    const change = Math.floor(Math.random() * 3) * this.direction;
    this.mainBusPassengers = Math.max(
      0,
      Math.min(50, this.mainBusPassengers + change)
    );

    if (Math.random() > 0.95) {
      this.currentStop = (this.currentStop + 1) % this.stops.length;
    }

    // Ensure occupancy is calculated correctly
    const occupancy = Math.round((this.mainBusPassengers / 50) * 100);

    return {
      passengers: this.mainBusPassengers,
      occupancy: occupancy,
      currentStop: this.stops[this.currentStop],
      nextStop: this.stops[(this.currentStop + 1) % this.stops.length],
    };
  }
}

const simulator = new BusDataSimulator();

// Update dashboard data
function updateDashboardData() {
  const data = simulator.update();

  // Update bus info
  document.getElementById(
    "bus-passengers"
  ).textContent = `${data.passengers}/50`;
  document.getElementById(
    "bus-location"
  ).textContent = `Near ${data.currentStop}`;
  document.getElementById("bus-next-stop").textContent = `${
    data.nextStop
  } (${Math.floor(Math.random() * 10 + 1)} min)`;
  document.getElementById(
    "occupancy-percent"
  ).textContent = `${data.occupancy}%`;

  const occupancyBar = document.getElementById("bus-occupancy-bar");
  occupancyBar.style.width = `${data.occupancy}%`;

  // Update status
  let status, statusClass;
  if (data.occupancy >= 80) {
    status = "OVERCROWDED";
    statusClass = "danger";
  } else if (data.occupancy >= 60) {
    status = "NEARLY FULL";
    statusClass = "warning";
  } else {
    status = "NORMAL";
    statusClass = "success";
  }

  const statusBadge = document.getElementById("bus-status-badge");
  statusBadge.textContent = status;
  statusBadge.className = `status-badge ${statusClass}`;
  occupancyBar.className = `progress-fill ${statusClass}`;

  // Update passenger value color
  const passengersElement = document.getElementById("bus-passengers");
  passengersElement.className =
    statusClass === "danger" ? "value large" : "value";

  // Update stats
  animateValue(
    "total-passengers",
    847,
    847 + Math.floor(Math.random() * 50),
    1000
  );
  animateValue("active-buses", 12, 12 + Math.floor(Math.random() * 3), 1000);

  // Update fleet occasionally
  if (Math.random() > 0.8) {
    fleetBuses.forEach((bus) => {
      bus.passengers = Math.max(
        0,
        Math.min(
          bus.capacity,
          bus.passengers + Math.floor(Math.random() * 5 - 2)
        )
      );
      const occupancy = bus.passengers / bus.capacity;
      bus.status =
        occupancy >= 0.8 ? "danger" : occupancy >= 0.6 ? "warning" : "normal";
    });
    renderFleetBuses();
  }

  // Update boardings/alightings
  document.getElementById("total-boardings").textContent =
    127 + Math.floor(Math.random() * 10);
  document.getElementById("total-alightings").textContent =
    84 + Math.floor(Math.random() * 10);
}

// Animate number changes
function animateValue(id, start, end, duration) {
  const element = document.getElementById(id);
  if (!element) return;

  const range = end - start;
  const increment = range / (duration / 16);
  let current = start;

  const timer = setInterval(() => {
    current += increment;
    if (
      (increment > 0 && current >= end) ||
      (increment < 0 && current <= end)
    ) {
      element.textContent = end;
      clearInterval(timer);
    } else {
      element.textContent = Math.floor(current);
    }
  }, 16);
}

// Initialize alerts
function initializeAlerts() {
  const initialAlerts = [
    {
      type: "danger",
      title: "BUS-138-CMB Overcrowded",
      desc: "50/50 passengers at Maradana",
      time: "Just now",
    },
    {
      type: "warning",
      title: "BUS-142-CMB Nearly Full",
      desc: "38/50 passengers approaching Maradana",
      time: "5 minutes ago",
    },
    {
      type: "info",
      title: "BUS-156-CMB Low Occupancy",
      desc: "12/50 passengers - Consider rerouting",
      time: "8 minutes ago",
    },
  ];

  initialAlerts.forEach((alert) => addAlert(alert, false));
}

// Add new alert with animation
function addAlert(alertData, animate = true) {
  const container = document.getElementById("alerts-container");

  // Create alert element
  const alertDiv = document.createElement("div");
  alertDiv.className = `alert-item ${alertData.type}`;
  if (animate) alertDiv.style.opacity = "0";

  alertDiv.innerHTML = `
    <div class="alert-title">${alertData.title}</div>
    <div class="alert-desc">${alertData.desc}</div>
    <div class="time-stamp">${alertData.time || "Just now"}</div>
  `;

  // Add to container
  container.insertBefore(alertDiv, container.firstChild);

  if (animate) {
    setTimeout(() => (alertDiv.style.opacity = "1"), 10);
  }

  // Remove oldest alert if exceeding max
  const alerts = container.querySelectorAll(".alert-item");
  if (alerts.length > maxAlerts) {
    const oldestAlert = alerts[alerts.length - 1];
    oldestAlert.classList.add("removing");
    setTimeout(() => oldestAlert.remove(), 300);
  }

  updateAlertCount();
}

// Update alert count
function updateAlertCount() {
  const count = document.querySelectorAll(
    "#alerts-container .alert-item"
  ).length;
  document.getElementById("alert-count").textContent = count;
}

// Generate random alert
function generateRandomAlert() {
  const alerts = [
    {
      type: "danger",
      title: "BUS-145-CMB Overcrowded",
      desc: "48/50 passengers at Maradana",
    },
    {
      type: "warning",
      title: "BUS-139-CMB Nearly Full",
      desc: "35/50 passengers approaching Borella",
    },
    {
      type: "info",
      title: "BUS-151-CMB Low Occupancy",
      desc: "8/50 passengers - Available capacity",
    },
    {
      type: "danger",
      title: "BUS-163-CMB Overcrowded",
      desc: "49/50 passengers at Fort Station",
    },
    {
      type: "warning",
      title: "BUS-171-CMB Filling Up",
      desc: "32/50 passengers at Narahenpita",
    },
  ];

  const alert = alerts[Math.floor(Math.random() * alerts.length)];
  addAlert(alert);
}

// Initialize animations
function initializeAnimations() {
  // Set initial animation states
  document.querySelectorAll(".stat-card").forEach((card, index) => {
    card.style.setProperty("--index", index);
  });

  renderFleetBuses();
}

// Start real-time updates
function startRealTimeUpdates() {
  setInterval(updateDashboardData, 3000);
  setInterval(generateRandomAlert, 15000);
  setInterval(updateTimeStamps, 60000);
  setInterval(animateMapBuses, 5000); // Animate map buses

  updateDashboardData();
}

// Animate bus markers on map
function animateMapBuses() {
  const markers = document.querySelectorAll(".bus-marker");
  markers.forEach((marker, index) => {
    const currentTop = parseFloat(marker.style.top);
    const currentLeft = parseFloat(marker.style.left);

    // Small random movement to simulate bus movement
    const newTop = Math.max(
      10,
      Math.min(90, currentTop + (Math.random() * 10 - 5))
    );
    const newLeft = Math.max(
      10,
      Math.min(90, currentLeft + (Math.random() * 10 - 5))
    );

    marker.style.transition = "top 4s ease, left 4s ease";
    marker.style.top = newTop + "%";
    marker.style.left = newLeft + "%";
  });
}

// Update time stamps
function updateTimeStamps() {
  document.querySelectorAll(".time-stamp").forEach((stamp) => {
    const text = stamp.textContent;
    if (text === "Just now") {
      stamp.textContent = "1 minute ago";
    } else if (text.includes("minute")) {
      const minutes = parseInt(text) + 1;
      stamp.textContent = `${minutes} minutes ago`;
    }
  });
}

// Export API
window.dashboardAPI = {
  updateBusData: updateDashboardData,
  addAlert: addAlert,
  toggleTheme: toggleTheme,
  clearAlerts: clearAlerts,
};
