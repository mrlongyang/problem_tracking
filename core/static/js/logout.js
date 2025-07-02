// <!-- 🔒 Logout Confirmation with SweetAlert2 -->

function confirmLogout(event) {
  event.preventDefault();
  Swal.fire({
    title: 'Log out?',
    text: 'Are you sure you want to log out?',
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#3085d6',
    cancelButtonColor: '#6c757d',
    confirmButtonText: 'ອອກ',
    cancelButtonText: 'ຍົກເລີກ'
  }).then((result) => {
    if (result.isConfirmed) {
      document.getElementById('logoutForm').submit();
    }
  });
}


// <!-- 🔍 Search filter & profile toggle -->
// Search filter
const input = document.getElementById('searchInput');
input.addEventListener('keyup', () => {
  const filter = input.value.toLowerCase();
  document.querySelectorAll('#problemTable tbody tr').forEach(row => {
    row.style.display = row.textContent.toLowerCase().includes(filter) ? '' : 'none';
  });
});

// Profile dropdown
const icon = document.getElementById('profileIcon');
const dropdown = document.getElementById('profileDropdown');
icon.addEventListener('click', () => {
  dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
});
window.addEventListener('click', e => {
  if (!icon.contains(e.target) && !dropdown.contains(e.target)) {
    dropdown.style.display = 'none';
  }
});