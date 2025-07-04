// Profile dropdown toggle
document.getElementById("profileIcon").addEventListener("click", function () {
     const dropdown = document.getElementById("profileDropdown");
     dropdown.style.display = dropdown.style.display === "flex" ? "none" : "flex";
});

// Logout confirmation
function confirmLogout(e) {
     e.preventDefault();
     Swal.fire({
          title: 'ອອກຈາກລະບົບ?',
          text: "ທ່ານຕ້ອງການອອກຈາກລະບົບບໍ່?",
          icon: 'warning',
          showCancelButton: true,
          confirmButtonColor: '#007bff',
          cancelButtonColor: '#d33',
          confirmButtonText: 'Yes, Logout'
     }).then((result) => {
          if (result.isConfirmed) {
               document.getElementById("logoutForm").submit();
          }
     });
}

// Simple search filter
document.getElementById("searchInput").addEventListener("keyup", function () {
     const value = this.value.toLowerCase();
     const rows = document.querySelectorAll("#problemTable tbody tr");
     rows.forEach(row => {
          row.style.display = row.innerText.toLowerCase().includes(value) ? "" : "none";
     });
});

document.addEventListener("DOMContentLoaded", function () {
     const urlParams = new URLSearchParams(window.location.search);
     const priority = urlParams.get("priority");
     const button = document.getElementById("priorityDropdownBtn");

     if (priority) {
          button.textContent = `Sort by: ${priority}`;
     } else {
          button.textContent = "Sort by: All";
     }
});