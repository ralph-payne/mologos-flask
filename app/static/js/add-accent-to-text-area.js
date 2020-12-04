/* Script to add an accent to the example text area when that accent is clicked on by user */

const addAccentToTextArea = event => {
    // Add accent to the text area
    document.getElementById("edited-example").value += event.value;
}
