/**
 * Custom Modal Functions
 * This script provides custom modal functionality with the new turquoise-blue theme
 */

// Function to create a custom confirmation modal
function showConfirmationModal(title, message, confirmCallback, cancelCallback) {
  // Use SweetAlert2 with our custom styling
  Swal.fire({
    title: title,
    text: message,
    icon: "question",
    showCancelButton: true,
    confirmButtonColor: "#1eacac", // Primary turquoise color
    cancelButtonColor: "#f44336", // Red for cancel
    confirmButtonText: "Yes, proceed!",
    cancelButtonText: "Cancel",
    borderRadius: "12px",
  }).then((result) => {
    if (result.isConfirmed && typeof confirmCallback === "function") {
      confirmCallback()
    } else if (typeof cancelCallback === "function") {
      cancelCallback()
    }
  })
}

// Function to show a success modal
function showSuccessModal(title, message, callback) {
  Swal.fire({
    title: title,
    text: message,
    icon: "success",
    confirmButtonColor: "#1eacac", // Primary turquoise color
    timer: 3000,
    timerProgressBar: true,
  }).then(() => {
    if (typeof callback === "function") {
      callback()
    }
  })
}

// Function to show an error modal
function showErrorModal(title, message) {
  Swal.fire({
    title: title,
    text: message,
    icon: "error",
    confirmButtonColor: "#1eacac", // Primary turquoise color
  })
}

// Function to show a loading modal
function showLoadingModal(title, message) {
  Swal.fire({
    title: title,
    text: message,
    allowOutsideClick: false,
    showConfirmButton: false,
    willOpen: () => {
      Swal.showLoading()
    },
  })
}

// Function to close any open modal
function closeModal() {
  Swal.close()
}

// Make functions available globally
window.showConfirmationModal = showConfirmationModal
window.showSuccessModal = showSuccessModal
window.showErrorModal = showErrorModal
window.showLoadingModal = showLoadingModal
window.closeModal = closeModal

