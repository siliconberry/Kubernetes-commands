<?php
// Target URL for redirection
$newUrl = "https://new-vm.example.com"; // Replace with your new VM's URL

// Display a message to the user
echo "<h1>This site has been migrated to a new VM</h1>";
echo "<p>You will be redirected to the new VM in <span id='countdown'>5</span> seconds...</p>";

// Use JavaScript for the countdown and redirection
echo "
<script>
    // Countdown timer
    let timeLeft = 5;
    const countdownElement = document.getElementById('countdown');

    const countdownInterval = setInterval(() => {
        timeLeft--;
        countdownElement.textContent = timeLeft;

        if (timeLeft <= 0) {
            clearInterval(countdownInterval);
            window.location.href = '$newUrl'; // Redirect to the new URL
        }
    }, 1000);
</script>
";

// Optional: Fallback redirection using meta refresh in case JavaScript is disabled
echo "<noscript><meta http-equiv='refresh' content='5;url=$newUrl'></noscript>";
?>
