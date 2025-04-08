function showNotification(message, color) {
    const notification = document.createElement('div');
    notification.textContent = message;
    notification.style.background = color;
    notification.style.color = '#fff';
    notification.style.padding = '15px';
    notification.style.margin = '10px';
    notification.style.borderRadius = '8px';
    notification.style.textAlign = 'center';
    notification.style.fontWeight = 'bold';
    notification.style.fontSize = '18px';
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.left = '50%';
    notification.style.transform = 'translateX(-50%)';
    notification.style.zIndex = '1000';
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 3000);
}

let redirected = false;

function checkRedirect() {
    fetch('/check_redirect')
        .then(response => response.json())
        .then(data => {
            if (data.redirect && !redirected) {
                redirected = true;
                showNotification("Face recognized! Redirecting to class...", "#28a745");
                setTimeout(() => {
                    window.location.href = "https://meet.jit.si/YourRoomName"; // 🔁 Change this to your Jitsi room
                }, 3000);
            }
        })
        .catch(err => console.error("Redirect check failed", err));
}

// Start polling every 3 seconds
setInterval(checkRedirect, 3000);
