// Update current time every second
function updateLastUpdated() {
  const now = new Date();
  const timeStr = now.toLocaleString();
  document.getElementById("lastUpdatedTime").textContent = timeStr;
}
setInterval(updateLastUpdated, 1000);
window.onload = updateLastUpdated;

// Add hover effect to cards
document.addEventListener("DOMContentLoaded", function () {
  const cards = document.querySelectorAll(".card");
  cards.forEach(card => {
    card.style.transition = "transform 0.3s ease";
    
    card.addEventListener("mouseenter", () => {
      card.style.transform = "scale(1.03)";
      card.style.boxShadow = "0 0 15px rgba(0, 0, 0, 0.2)";
    });

    card.addEventListener("mouseleave", () => {
      card.style.transform = "scale(1)";
      card.style.boxShadow = "none";
    });
  });

  // Highlight active menu item
  const currentPath = window.location.pathname;
  const navLinks = document.querySelectorAll('.nav-link');
  navLinks.forEach(link => {
    if (link.getAttribute('href') === currentPath) {
      link.classList.add('active');
      link.style.fontWeight = 'bold';
      link.style.color = '#00c6ff';
    }
  });
});

 
// Show current date/time in Last Updated card
function updateLastUpdated() {
  const now = new Date();
  const timeStr = now.toLocaleString();
  document.getElementById("lastUpdatedTime").textContent = timeStr;
}

// Update when page loads
window.onload = updateLastUpdated;