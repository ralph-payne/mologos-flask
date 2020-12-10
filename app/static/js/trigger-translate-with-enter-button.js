/* Script to Trigger Translate on Pressing Enter Button */

// Get the input field
const textBoxInput = document.getElementById("text-to-translate");

// Execute a function when the user releases a key on the keyboard
textBoxInput.addEventListener("keydown", function(event) {
    
    // Number 13 is the "Enter" key on the keyboard
    if (event.keyCode === 13) {
        // Cancel the default action, if needed
        event.preventDefault();
        
        // Trigger the button element with a click
        document.getElementById("translate-btn").click();
    }
});
