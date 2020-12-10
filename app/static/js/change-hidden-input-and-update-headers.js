/* Script which listens for when the select element gets changed and then updates the hidden value */
/* This script is used on the Upload Page */

const changeHiddenInputToLanguageSelectedAndUpdateHeaders = () => {
    let hiddenElementToSendToServer = document.getElementById("most-recent-translation-lang").value;

    selectLanguage = document.getElementById("select-language");

    // Assign the hidden element the value of the most recently used language
    hiddenElementToSendToServer = selectLanguage.value;

    // Grab the value of the language selected
    languageSelected = selectLanguage.options[selectLanguage.selectedIndex].text;

    console.log(languageSelected);
    console.log('laskdjflkj');

    // Update the headings
    if (languageSelected === "English") {
        document.getElementById("upload-2-header").innerHTML = "Example Sentences";
        document.getElementById("upload-3-header").innerHTML = "Target Words";
    } else {
        document.getElementById("upload-2-header").innerHTML = "English";
        document.getElementById("upload-3-header").innerHTML = languageSelected;
    }
}