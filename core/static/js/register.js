// Simple input focus animation (optional)
document.addEventListener('DOMContentLoaded', () => {
  const inputs = document.querySelectorAll('.form-control');
  inputs.forEach(input => {
    input.addEventListener('focus', () => {
      input.style.border = '2px solid #00c6ff';
    });
    input.addEventListener('blur', () => {
      input.style.border = 'none';
    });
  });
});
