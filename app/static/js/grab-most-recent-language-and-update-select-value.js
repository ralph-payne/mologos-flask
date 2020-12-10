/* Script which grabs the most recent language the user has used and updates the select value */
/* This script is used on the Upload Page */


// Get Most recent language from hidden input
const mostRecentLanguage = document.getElementById("most-recent-translation-lang").value;

// Declare function
const selectFromOptions = (selectId, optionValToSelect) => {
    
    // Get the select element by its unique ID.
    const selectElement = document.getElementById(selectId);

    // Get the options.
    const selectOptions = selectElement.options;

    // Loop through these options using a for loop.
    for (let option, i = 0; option = selectOptions[i]; i++) {
        //If the option of value is equal to the option we want to select.
        if (option.value == optionValToSelect) {
            //Select the option and break out of the for loop.
            selectElement.selectedIndex = i;
            break;
        }
    }
}

// Call function
selectFromOptions("select-language", mostRecentLanguage);

// Display the block which was previously hidden (This prevents stutterly loading)
document.getElementById("language-select-container").style.display = "block";

changeHiddenInputToLanguageSelectedAndUpdateHeaders();