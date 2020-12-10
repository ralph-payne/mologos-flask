/* Script which toggles the value of the switch element on change */
const toggleValOfSwitchElementOnChange = (element) => {
    // If the value is 1, switch
    // All input values are strings. They can be converted to ints on the backend
    if (element.previousElementSibling.value == "1")
    {
        element.previousElementSibling.value = "0";
    }
    else
    {
        element.previousElementSibling.value = "1";
    }
}