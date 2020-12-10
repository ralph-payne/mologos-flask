const displayLanguageSelectContainerOnWindowLoad = () => {
    const languageSelectContainer = document.getElementById('language-select-container')

    languageSelectContainer.style.display = 'block';
}

window.onload = displayLanguageSelectContainerOnWindowLoad();