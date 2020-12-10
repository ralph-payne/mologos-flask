/* Script which listens for changes to the select element and then updates the headings */
selectLanguage = document.getElementById("select-language");

selectLanguage.onchange = () => {
    changeHiddenInputToLanguageSelectedAndUpdateHeaders();
}
