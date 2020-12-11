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



/*
on keyDown anywhere,

Inside of the div write the function for listneing to on key down

the function accdepts one parameter

athat parameter is the id of the button that you want to fire off when the user pressees enter


 fireSubmitOnEnter(this, "translate-btn")




*/


/* Not currently working */
const fireSubmitOnEnter = (event, idOfButton) => {

    console.log(idOfButton)

    console.log(event.key)

    event.keyCode

    if (event.keyCode === 13) {
        event.preventDefault();

        document.getElementById(idOfButton).click();

    }

}