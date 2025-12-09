/* -----------------------------------------
   Flash Auto Close
------------------------------------------ */
// Auto-dismiss alerts after 4 seconds
setTimeout(() => {
    document.querySelectorAll(".alert").forEach(alert => {
        let bsAlert = new bootstrap.Alert(alert);
        bsAlert.close();
    });
}, 4000);


/* -----------------------------------------
   Confirm Dialog for Destructive Actions
------------------------------------------ */

// Add confirm to any element with class="confirm-action"
document.querySelectorAll(".confirm-action").forEach(btn => {
    btn.addEventListener("click", function (e) {
        if (!confirm("Are you sure? This action cannot be undone.")) {
            e.preventDefault();
        }
    });
});


/* -----------------------------------------
   AJAX POST Helper (Optional)
------------------------------------------ */
async function postJSON(url, data) {
    try {
        const res = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });

        return res.json();
    } catch (err) {
        console.error("POST error:", err);
        return { error: "Request failed" };
    }
}


/* -----------------------------------------
   Active Navbar Highlight
------------------------------------------ */
const currentPath = window.location.pathname;

document.querySelectorAll(".nav-link").forEach(link => {
    if (link.getAttribute("href") === currentPath) {
        link.classList.add("active");
        link.classList.add("fw-semibold");
    }
});


/* -----------------------------------------
   Smooth Scroll Utility (if needed)
------------------------------------------ */
function smoothScrollTo(id) {
    const el = document.getElementById(id);
    if (el) {
        window.scrollTo({
            top: el.offsetTop - 100,
            behavior: "smooth"
        });
    }
}
